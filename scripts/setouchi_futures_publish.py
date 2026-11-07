"""Read/plan/apply WordPress gallery updates, preserving content outside the group."""
from hashlib import sha256
import json
import mimetypes
import os
from pathlib import Path
import re
import shlex
import subprocess
from urllib.parse import quote, urljoin, urlsplit

from bs4 import BeautifulSoup
import requests

from setouchi_futures import SCHEMA, digest, gallery_blocks, write_json


def text_hash(value):
    return sha256(value.encode('utf-8')).hexdigest()


def private_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    previous = os.umask(0o077)
    try:
        write_json(path, value)
        path.chmod(0o600)
    finally:
        os.umask(previous)


def page_text(page):
    raw = page.get('content', {}).get('raw')
    if not isinstance(raw, str):
        raise ValueError('An authenticated context=edit page with content.raw is required')
    return raw


def page_identity(page):
    identity = {key: page.get(key) for key in ('id', 'link', 'status', 'slug', 'parent', 'template')}
    identity['title'] = page.get('title', {}).get('raw')
    return identity


def validate_page(page, config):
    if page.get('id') != config['page_id'] or page.get('link', '').rstrip('/') != config['page_url'].rstrip('/'):
        raise ValueError('Page ID/permalink does not match the approved Setouchi destination')
    page_text(page)


def parse_blocks(content):
    """Locate complete serialized core blocks without rewriting their HTML."""
    pattern = re.compile(r'<!--\s*(/?)wp:([\w/-]+)(.*?)-->', re.S)
    stack, blocks = [], []
    for match in pattern.finditer(content):
        closing, name, tail = match.groups()
        if closing:
            if not stack or stack[-1]['name'] != name:
                raise ValueError('Unbalanced WordPress blocks; refusing to patch')
            block = stack.pop()
            block['end'] = match.end()
            blocks.append(block)
        else:
            attrs_text = tail.strip()
            self_closing = attrs_text.endswith('/')
            if self_closing:
                attrs_text = attrs_text[:-1].strip()
            attrs = json.loads(attrs_text) if attrs_text else {}
            block = {'name': name, 'attrs': attrs, 'start': match.start(), 'end': match.end()}
            if self_closing:
                blocks.append(block)
            else:
                stack.append(block)
    if stack:
        raise ValueError('Unclosed WordPress blocks; refusing to patch')
    return blocks


def patch_gallery(content, fragment, config):
    headings = []
    for match in re.finditer(r'<(h2|p)\b[^>]*>.*?</\1\s*>', content, re.I | re.S):
        node = BeautifulSoup(match.group(), 'html.parser').find(match[1].lower())
        value = ' '.join(node.get_text(' ', strip=True).split())
        if node.name == 'p':
            bold = node.find(['b', 'strong'])
            if bold is None or ' '.join(bold.get_text(' ', strip=True).split()) != value:
                continue
        if value == config['insertion_heading']:
            headings.append(match)
    if len(headings) != 1:
        raise ValueError('Expected one exact insertion heading; found ' + str(len(headings)))
    heading = headings[0]
    try:
        blocks = parse_blocks(content)
    except ValueError:
        if heading[1].lower() != 'p':
            raise
        # Classic-editor pages can have malformed block comments later in the
        # article. Only accept a complete block prefix before a standalone bold
        # paragraph; the suffix is preserved byte-for-byte, never repaired here.
        blocks = parse_blocks(content[:heading.start()])
    managed = [b for b in blocks if b['name'] == 'group' and b['attrs'].get('anchor') == config['anchor']]
    if len(managed) > 1:
        raise ValueError('Duplicate managed gallery blocks')
    anchors = BeautifulSoup(content, 'html.parser').find_all(id=config['anchor'])
    if len(anchors) > 1:
        raise ValueError('Duplicate gallery HTML anchors')
    if managed:
        old = managed[0]
        if old['end'] > heading.start():
            raise ValueError('Managed gallery is not before the insertion heading')
        if not BeautifulSoup(content[old['start']:old['end']], 'html.parser').find(id=config['anchor']):
            raise ValueError('Managed Group is missing its gallery HTML anchor')
        return content[:old['start']] + fragment.rstrip() + content[old['end']:]
    # A matching HTML ID outside the managed group is not ours to replace.
    if anchors:
        raise ValueError('Gallery anchor exists outside the managed Group block')
    insertion = heading.start()
    owners = [b for b in blocks if b['name'] in ('heading', 'paragraph') and b['start'] <= insertion < b['end']]
    if owners:
        insertion = min(b['start'] for b in owners)
    before = BeautifulSoup(content[:insertion], 'html.parser')
    lists = [node for node in before.find_all(['ul', 'ol']) if not node.find_parent(['ul', 'ol'])]
    if len(lists) < config['preceding_list_count']:
        items = lists[0].find_all('li', recursive=False) if len(lists) == 1 else []
        linked_items = (len(items) == config['preceding_list_count'] and all(
            not item.find(['ul', 'ol']) and len(item.find_all('a', href=True)) == 1
            and item.get_text(' ', strip=True) == item.find('a').get_text(' ', strip=True)
            for item in items))
        if not linked_items:
            raise ValueError('The current page does not contain the expected three preceding lists or linked atlas items')
    return content[:insertion] + fragment.rstrip() + '\n\n' + content[insertion:]


def media_url(remote, key):
    """Link detail images to the original when WordPress makes a scaled copy."""
    url = remote.get('source_url', '')
    if urlsplit(url).scheme != 'https':
        raise ValueError('WordPress returned a non-HTTPS media URL')
    original = remote.get('media_details', {}).get('original_image')
    if key.endswith('-detail') and original:
        if not isinstance(original, str) or '/' in original or '\\' in original or original in ('.', '..'):
            raise ValueError('WordPress returned an invalid original image filename')
        url = urljoin(url, quote(original, safe=''))
    return url


def load_prepared(directory):
    directory = Path(directory).resolve()
    prepared = json.loads((directory / 'prepared.json').read_text())
    if prepared.get('schema') != SCHEMA:
        raise ValueError('Unsupported prepared bundle')
    for asset in prepared['assets']:
        path = (directory / asset['path']).resolve()
        if not path.is_relative_to(directory) or path.suffix not in ('.jpg', '.webp', '.pdf'):
            raise ValueError('Asset path leaves the prepared bundle or has an unsupported type')
        if digest(path) != asset['sha256']:
            raise ValueError('Prepared asset checksum changed: ' + asset['key'])
    return prepared


def used_keys(prepared):
    return set(re.findall(r'\{\{asset:([^}]+)\}\}', gallery_blocks(prepared)))


class RestBackend:
    def __init__(self, config, credentials=None):
        self.config = config
        site = config['site_url'].rstrip('/')
        parsed = urlsplit(site)
        if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('The WordPress API requires an HTTPS site origin')
        if urlsplit(config['page_url']).netloc != parsed.netloc:
            raise ValueError('Page and API hosts differ')
        values = {}
        if credentials:
            path = Path(credentials)
            if path.stat().st_mode & 0o077:
                raise ValueError('Credential file must be private (chmod 600)')
            values = json.loads(path.read_text())
        username = values.get('username') or os.environ.get('WP_USERNAME')
        password = values.get('application_password') or os.environ.get('WP_APPLICATION_PASSWORD')
        if not username or not password:
            raise ValueError('Set WP_USERNAME and WP_APPLICATION_PASSWORD, or use --credentials-file')
        self.base = site + '/wp-json/wp/v2/'
        self.session = requests.Session()
        self.session.auth = (username, password)

    def request(self, method, path, **kwargs):
        response = self.session.request(method, self.base + path, timeout=90, allow_redirects=False, **kwargs)
        if not response.ok or response.is_redirect:
            # Do not dump requests, authorization headers, or server HTML into logs.
            raise RuntimeError(f'WordPress {method} {path.split("?")[0]} returned HTTP {response.status_code}')
        try:
            return response.json()
        except ValueError as error:
            raise RuntimeError('WordPress returned a non-JSON response') from error

    def get_page(self):
        return self.request('GET', f'pages/{self.config["page_id"]}', params={'context': 'edit'})

    def find_media(self, slug):
        records = self.request('GET', 'media', params={'slug': slug, 'context': 'edit'})
        if len(records) > 1:
            raise ValueError('Duplicate media slug on WordPress')
        return records[0] if records else None

    def upload(self, asset, path, slug):
        with path.open('rb') as stream:
            return self.request('POST', 'media', files={'file': (slug + path.suffix, stream, mimetypes.guess_type(path)[0])},
                data={'slug': slug, 'title': asset['title'], 'alt_text': asset['alt'], 'caption': asset['caption'],
                      'post': self.config['page_id']})

    def update(self, content, expected_hash):
        # The stock REST API has no atomic content-hash condition; recheck immediately before writing.
        if text_hash(page_text(self.get_page())) != expected_hash:
            raise ValueError('Page changed immediately before update; re-plan')
        return self.request('POST', f'pages/{self.config["page_id"]}', json={'content': content})


class WpCliBackend:
    def __init__(self, config, host=None, wp_path=None):
        self.config = config
        self.host = host or os.environ.get('WP_SSH_HOST')
        self.wp_path = wp_path or os.environ.get('WP_PATH')
        if not self.host or self.host.startswith('-') or not re.fullmatch(r'[\w.@:-]+', self.host) or not self.wp_path:
            raise ValueError('Set WP_SSH_HOST and WP_PATH, or provide --ssh-host and --wp-path')
        self.php = Path(__file__).with_name('setouchi_futures_wp.php').read_text()

    def call(self, op, **values):
        command = shlex.join(['wp', '--path=' + self.wp_path, 'eval', self.php])
        payload = {'op': op, 'page_id': self.config['page_id'], **values}
        result = subprocess.run(['ssh', '-o', 'BatchMode=yes', self.host, command],
                                input=json.dumps(payload), text=True, capture_output=True, timeout=120)
        if result.returncode:
            raise RuntimeError('WP-CLI transport failed (credentials and server output omitted)')
        try:
            value = json.loads(result.stdout)
        except ValueError as error:
            raise RuntimeError('WP-CLI did not return clean JSON') from error
        if isinstance(value, dict) and value.get('error'):
            raise RuntimeError('WP-CLI: ' + value['error'])
        return value

    def get_page(self):
        return self.call('get_page')

    def find_media(self, slug):
        return self.call('find_media', slug=slug)

    def upload(self, asset, path, slug):
        import base64
        return self.call('upload', slug=slug, filename=slug + path.suffix,
                         data=base64.b64encode(path.read_bytes()).decode('ascii'),
                         title=asset['title'], alt=asset['alt'], caption=asset['caption'])

    def update(self, content, expected_hash):
        return self.call('update', content=content, expected_hash=expected_hash)


def make_plan(directory, page, transport='rest', offline=False):
    directory = Path(directory).resolve()
    prepared = load_prepared(directory)
    config = prepared['config']
    validate_page(page, config)
    template = gallery_blocks(prepared)
    candidate = patch_gallery(page_text(page), template, config)
    plan = {'schema': 'cartofreako-setouchi-publish-plan-v1', 'bundle': str(directory),
            'prepared_sha256': digest(directory / 'prepared.json'), 'template_sha256': text_hash(template),
            'base_hash': text_hash(page_text(page)), 'identity': page_identity(page), 'transport': transport,
            'offline': offline, 'base_page': page,
            'media_keys': sorted(used_keys(prepared)), 'remote_writes': 0}
    target = directory / 'private/publish-plan.json'
    private_json(target, plan)
    (target.parent / 'page-before.html').write_text(page_text(page))
    (target.parent / 'page-planned.html').write_text(candidate)
    for p in [target.parent / 'page-before.html', target.parent / 'page-planned.html']:
        p.chmod(0o600)
    return target, plan


def check_base(page, plan, config):
    validate_page(page, config)
    if text_hash(page_text(page)) != plan['base_hash'] or page_identity(page) != plan['identity']:
        raise ValueError('Page content or metadata changed since the plan; re-plan')


def apply_plan(plan_path, backend):
    plan = json.loads(Path(plan_path).read_text())
    if plan.get('schema') != 'cartofreako-setouchi-publish-plan-v1':
        raise ValueError('Unsupported publish plan')
    directory = Path(plan['bundle'])
    prepared = load_prepared(directory)
    if digest(directory / 'prepared.json') != plan['prepared_sha256'] or text_hash(gallery_blocks(prepared)) != plan['template_sha256']:
        raise ValueError('Bundle or gallery template changed since planning; re-plan')
    config = prepared['config']
    check_base(backend.get_page(), plan, config)
    private = directory / 'private'
    backup_path = private / ('page-backup-' + plan['base_hash'][:16] + '.json')
    if not backup_path.exists():
        private_json(backup_path, {'schema': 'cartofreako-setouchi-page-backup-v1', 'config': config,
                     'page': plan['base_page'], 'transport': plan['transport'], 'expected_after_hash': None})
    state_path = private / 'media-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    assets = {a['key']: a for a in prepared['assets']}
    mapping = {}
    for key in plan['media_keys']:
        asset = assets[key]
        # A deterministic content-addressed slug allows recovery even after a lost local response/state file.
        slug = 'setouchi-' + key + '-' + asset['sha256'][:16]
        remote = backend.find_media(slug)
        if remote is None:
            remote = backend.upload(asset, directory / asset['path'], slug)
        if remote.get('slug') != slug or not isinstance(remote.get('id'), int):
            raise ValueError('Unexpected media identity returned by WordPress')
        url = media_url(remote, key)
        mapping[key] = {'id': remote['id'], 'url': url, 'sha256': asset['sha256'], 'slug': slug}
        state[key] = mapping[key]
        private_json(state_path, state)
    # Uploads can take time; keep other edits made during that interval.
    current = backend.get_page()
    check_base(current, plan, config)
    content = patch_gallery(page_text(current), gallery_blocks(prepared, media=mapping), config)
    receipt = {'schema': 'cartofreako-setouchi-publish-receipt-v1', 'bundle': str(directory), 'config': config,
               'transport': plan['transport'], 'identity': plan['identity'], 'backup': str(backup_path),
               'before_hash': plan['base_hash'], 'after_hash': text_hash(content),
               'media': mapping, 'page_changed': content != page_text(current), 'status': 'write-pending'}
    receipt_path = private / 'publish-receipt.json'
    private_json(receipt_path, receipt)
    if receipt['page_changed']:
        backend.update(content, plan['base_hash'])
    after = backend.get_page()
    receipt['observed_hash'] = text_hash(page_text(after))
    receipt['status'] = 'verified-content' if receipt['observed_hash'] == receipt['after_hash'] and page_identity(after) == plan['identity'] else 'verification-failed'
    private_json(receipt_path, receipt)
    backup = json.loads(backup_path.read_text())
    # An unexpected readback may include a human edit made after our write.
    # Never authorize restoration over content we cannot identify as our own.
    backup['expected_after_hash'] = receipt['after_hash'] if receipt['status'] == 'verified-content' else None
    private_json(backup_path, backup)
    if receipt['status'] != 'verified-content':
        raise RuntimeError('Page was written but readback differs; inspect the receipt and saved backup before retrying')
    return receipt_path, receipt


def verify_receipt(path, backend, public=False):
    receipt = json.loads(Path(path).read_text())
    page = backend.get_page()
    validate_page(page, receipt['config'])
    if text_hash(page_text(page)) != receipt['after_hash'] or page_identity(page) != receipt['identity']:
        raise ValueError('Published content/metadata no longer matches the receipt')
    result = {'content_matches': True, 'media_count': len(receipt['media']), 'public_checks': []}
    if public:
        urls = [receipt['config']['page_url']] + [m['url'] for m in receipt['media'].values()]
        for url in urls:
            try:
                with requests.get(url, stream=True, timeout=30) as response:
                    result['public_checks'].append({'url': url, 'status': response.status_code})
            except requests.RequestException:
                result['public_checks'].append({'url': url, 'status': 'unreachable'})
        result['public_access_verified'] = all(r['status'] == 200 for r in result['public_checks'])
    return result


def restore_backup(path, backend):
    backup = json.loads(Path(path).read_text())
    if backup.get('schema') != 'cartofreako-setouchi-page-backup-v1' or not backup.get('expected_after_hash'):
        raise ValueError('Backup has no verified post-update state to restore from')
    current = backend.get_page()
    validate_page(current, backup['config'])
    if page_identity(current) != page_identity(backup['page']) or text_hash(page_text(current)) != backup['expected_after_hash']:
        raise ValueError('Page changed after this update; refusing to overwrite subsequent edits')
    backend.update(page_text(backup['page']), backup['expected_after_hash'])
    after = backend.get_page()
    if text_hash(page_text(after)) != text_hash(page_text(backup['page'])) or page_identity(after) != page_identity(backup['page']):
        raise RuntimeError('Restore readback did not match the saved page')
    return {'restored': True, 'page_id': after['id']}
