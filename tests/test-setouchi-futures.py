#!/usr/bin/env python3
"""Exercise targeted WordPress updates, upload recovery, and saved-page restoration offline."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from setouchi_futures import SCHEMA, block, gallery_blocks, load_config, write_json
from setouchi_futures_publish import (RestBackend, WpCliBackend, apply_plan, load_prepared, make_plan,
    media_url, page_text, parse_blocks, patch_gallery, restore_backup, text_hash, verify_receipt)


class FakeWordPress:
    def __init__(self, page):
        self.page = deepcopy(page)
        self.media = {}
        self.uploads = 0
        self.updates = 0
        self.fail_upload = None
        self.edit_during_upload = False
        self.sanitize = False

    def get_page(self):
        return deepcopy(self.page)

    def find_media(self, slug):
        return deepcopy(self.media.get(slug))

    def upload(self, asset, path, slug):
        self.uploads += 1
        if self.uploads == self.fail_upload:
            raise RuntimeError('simulated media failure')
        media = {'id': len(self.media) + 100, 'slug': slug,
                 'source_url': 'https://benjamin.dekosnik.com/wp-content/uploads/' + slug + path.suffix}
        self.media[slug] = media
        if self.edit_during_upload:
            self.page['content']['raw'] += '<p>A newer human edit.</p>'
            self.edit_during_upload = False
        return deepcopy(media)

    def update(self, content, expected_hash):
        if text_hash(page_text(self.page)) != expected_hash:
            raise ValueError('stale page')
        self.updates += 1
        self.page['content']['raw'] = content + ('<!-- server filtered content -->' if self.sanitize else '')
        return self.get_page()


class FuturesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name)
        self.config = load_config()
        prefix = '<p>Keep my introduction &amp; punctuation.</p>\n'
        prefix += ''.join(block('list', f'<ul><li>Existing list {i}</li></ul>') for i in range(3))
        suffix = block('heading', '<h2 class="wp-block-heading">Two atlases, one shared table</h2>')
        suffix += '<p>Keep this latest atlas paragraph.</p>'
        self.prefix, self.suffix = prefix, suffix
        self.page = {'id': 3175, 'link': self.config['page_url'], 'status': 'draft', 'parent': 44,
                     'slug': 'setouchi-2028', 'template': 'custom.php', 'content': {'raw': prefix + suffix}}
        assets = []
        ids = [f'{scope}-{m["stem"]}' for scope in ('world', 'japan') for m in self.config['maps']]
        for ident in ids + [m['id'] for m in self.config['hamonshu']]:
            roles = ['640', '1280', 'detail'] + (['legend'] if ident in ids else [])
            for role in roles:
                key = ident + '-' + role
                path = self.bundle / ('media/' + key + ('.pdf' if role == 'legend' else '.webp'))
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(('offline fixture: ' + key).encode())
                assets.append({'key': key, 'path': path.relative_to(self.bundle).as_posix(),
                    'sha256': sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
                    'title': key, 'alt': 'Description', 'caption': 'Caption', 'width': 1280, 'height': 554})
        self.prepared = {'schema': SCHEMA, 'config': self.config, 'assets': assets, 'provenance': []}
        write_json(self.bundle / 'prepared.json', self.prepared)
        self.backend = FakeWordPress(self.page)

    def plan(self):
        return make_plan(self.bundle, self.backend.get_page())[0]

    def test_insertion_preserves_surrounding_content_exactly(self):
        fragment = gallery_blocks(self.prepared)
        result = patch_gallery(page_text(self.page), fragment, self.config)
        self.assertEqual(result, self.prefix + fragment.rstrip() + '\n\n' + self.suffix)
        self.assertEqual(sum(b['attrs'].get('anchor') == self.config['anchor'] for b in parse_blocks(result)), 1)

    def test_replacing_group_is_idempotent(self):
        fragment = gallery_blocks(self.prepared)
        one = patch_gallery(page_text(self.page), fragment, self.config)
        self.assertEqual(patch_gallery(one, fragment, self.config), one)

    def test_missing_or_duplicate_heading_stops(self):
        for content in [self.prefix, page_text(self.page) + self.suffix]:
            with self.assertRaisesRegex(ValueError, 'insertion heading'):
                patch_gallery(content, gallery_blocks(self.prepared), self.config)

    def test_missing_lists_stops(self):
        with self.assertRaisesRegex(ValueError, 'three preceding lists'):
            patch_gallery(self.suffix, gallery_blocks(self.prepared), self.config)

    def test_nested_list_is_not_counted_as_another_intro_list(self):
        source = '<ul><li>One<ul><li>Nested</li></ul></li></ul><ol><li>Two</li></ol>' + self.suffix
        with self.assertRaises(ValueError):
            patch_gallery(source, gallery_blocks(self.prepared), self.config)

    def test_foreign_anchor_and_misplaced_group_stop(self):
        fragment = gallery_blocks(self.prepared)
        for source in ['<div id="setouchi-futures-visuals"></div>' + page_text(self.page),
                       page_text(self.page) + fragment,
                       self.prefix + fragment + fragment + self.suffix]:
            with self.assertRaises(ValueError):
                patch_gallery(source, fragment, self.config)

    def test_malformed_blocks_stop(self):
        with self.assertRaises(ValueError):
            patch_gallery('<!-- wp:group -->' + page_text(self.page), gallery_blocks(self.prepared), self.config)

    def test_classic_title_and_three_linked_items_preserve_legacy_suffix(self):
        prefix = block('paragraph', '<p>Keep this introduction.</p>')
        prefix += '<ul>\r\n' + ''.join(f'<li><a href="/{i}.pdf">Atlas {i}</a></li>\r\n' for i in range(3)) + '</ul>\r\n'
        suffix = ('<p><b>Two atlases, one shared table</b></p>\r\n<p>Existing article.</p>\r\n'
                  '<!-- /wp:post-content -->\r\n<!-- wp:heading -->\r\n<p><b>Events</b></p>')
        source = prefix + suffix
        fragment = gallery_blocks(self.prepared)
        result = patch_gallery(source, fragment, self.config)
        self.assertEqual(result, prefix + fragment.rstrip() + '\n\n' + suffix)
        self.assertEqual(patch_gallery(result, fragment, self.config), result)
        replacement = fragment.replace('World</h3>', 'World atlas</h3>')
        self.assertEqual(patch_gallery(result, replacement, self.config), prefix + replacement.rstrip() + '\n\n' + suffix)
        with self.assertRaises(ValueError):
            patch_gallery('<!-- wp:group -->' + source, fragment, self.config)
        with self.assertRaises(ValueError):
            patch_gallery(source + '<div id="setouchi-futures-visuals"></div>', fragment, self.config)
        with self.assertRaises(ValueError):
            patch_gallery(source + '<p><strong>Two atlases, one shared table</strong></p>', fragment, self.config)

    def test_paragraph_block_title_inserts_before_its_wrapper(self):
        suffix = block('paragraph', '<p><strong>Two atlases, one shared table</strong></p>')
        fragment = gallery_blocks(self.prepared)
        result = patch_gallery(self.prefix + suffix, fragment, self.config)
        self.assertEqual(result, self.prefix + fragment.rstrip() + '\n\n' + suffix)
        parse_blocks(result)

    def test_prose_or_unlinked_items_are_not_an_insertion_boundary(self):
        fragment = gallery_blocks(self.prepared)
        for title in ['<p>Two atlases, one shared table</p>',
                      '<p><b>Two atlases</b>, one shared table</p>']:
            with self.assertRaisesRegex(ValueError, 'insertion heading'):
                patch_gallery(self.prefix + title, fragment, self.config)
        prefix = '<ul><li>One</li><li>Two</li><li>Three</li></ul>'
        with self.assertRaises(ValueError):
            patch_gallery(prefix + '<p><b>Two atlases, one shared table</b></p>', fragment, self.config)

    def test_detail_url_uses_original_image_metadata(self):
        remote = {'source_url': 'https://example.test/uploads/map-scaled.webp',
                  'media_details': {'original_image': 'map.webp'}}
        self.assertEqual(media_url(remote, 'world-water-detail'), 'https://example.test/uploads/map.webp')
        self.assertEqual(media_url(remote, 'world-water-1280'), remote['source_url'])
        self.assertEqual(media_url({'source_url': remote['source_url']}, 'world-water-detail'), remote['source_url'])
        remote['media_details']['original_image'] = '../elsewhere.webp'
        with self.assertRaises(ValueError):
            media_url(remote, 'world-water-detail')

    def test_plan_is_local_read_only_and_private(self):
        path = self.plan()
        self.assertEqual(self.backend.uploads, 0)
        self.assertEqual(self.backend.updates, 0)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(json.loads(path.read_text())['media_keys']), 36)

    def test_stale_page_stops_before_upload(self):
        plan = self.plan()
        self.backend.page['content']['raw'] += '<p>New human edit.</p>'
        with self.assertRaisesRegex(ValueError, 'changed since'):
            apply_plan(plan, self.backend)
        self.assertEqual(self.backend.uploads, 0)
        self.assertEqual(self.backend.updates, 0)

    def test_changed_metadata_stops_before_upload(self):
        plan = self.plan()
        self.backend.page['status'] = 'publish'
        with self.assertRaises(ValueError):
            apply_plan(plan, self.backend)
        self.assertEqual(self.backend.uploads, 0)

    def test_changed_title_requires_a_new_plan(self):
        plan = self.plan()
        self.backend.page['title'] = {'raw': 'A later title edit'}
        with self.assertRaises(ValueError):
            apply_plan(plan, self.backend)
        self.assertEqual(self.backend.updates, 0)

    def test_failed_upload_keeps_page_and_recovers_without_duplicates(self):
        plan = self.plan()
        self.backend.fail_upload = 3
        with self.assertRaisesRegex(RuntimeError, 'media failure'):
            apply_plan(plan, self.backend)
        self.assertEqual(page_text(self.backend.page), page_text(self.page))
        self.assertEqual(self.backend.updates, 0)
        self.assertEqual(len(self.backend.media), 2)
        self.backend.fail_upload = None
        _, receipt = apply_plan(plan, self.backend)
        self.assertEqual(len(self.backend.media), 36)
        self.assertEqual(self.backend.uploads, 37)  # 36 successful uploads and the one failed attempt.
        self.assertEqual(receipt['status'], 'verified-content')

    def test_concurrent_edit_during_upload_is_preserved(self):
        plan = self.plan()
        self.backend.edit_during_upload = True
        with self.assertRaisesRegex(ValueError, 'changed since'):
            apply_plan(plan, self.backend)
        self.assertEqual(self.backend.updates, 0)
        self.assertIn('newer human edit', page_text(self.backend.page))

    def test_publish_rerun_is_a_noop_and_preserves_metadata(self):
        path, receipt = apply_plan(self.plan(), self.backend)
        self.assertEqual(self.backend.page['status'], 'draft')
        self.assertEqual(self.backend.page['parent'], 44)
        self.assertEqual(self.backend.page['template'], 'custom.php')
        self.assertTrue(verify_receipt(path, self.backend)['content_matches'])
        _, second = apply_plan(self.plan(), self.backend)
        self.assertEqual(self.backend.uploads, 36)
        self.assertEqual(self.backend.updates, 1)
        self.assertFalse(second['page_changed'])
        self.assertEqual(second['status'], 'verified-content')

    def test_restore_round_trip_preserves_original_page(self):
        _, receipt = apply_plan(self.plan(), self.backend)
        restore_backup(receipt['backup'], self.backend)
        self.assertEqual(self.backend.page, self.page)

    def test_restore_will_not_overwrite_later_human_edit(self):
        _, receipt = apply_plan(self.plan(), self.backend)
        self.backend.page['content']['raw'] += '<p>Keep this later edit.</p>'
        with self.assertRaisesRegex(ValueError, 'subsequent edits'):
            restore_backup(receipt['backup'], self.backend)

    def test_server_filtering_is_reported_after_write(self):
        self.backend.sanitize = True
        with self.assertRaisesRegex(RuntimeError, 'written but readback differs'):
            apply_plan(self.plan(), self.backend)
        receipt = json.loads((self.bundle / 'private/publish-receipt.json').read_text())
        self.assertEqual(receipt['status'], 'verification-failed')
        self.assertTrue(Path(receipt['backup']).exists())

    def test_edit_before_readback_cannot_be_automatically_restored_over(self):
        original_update = self.backend.update

        def update_then_edit(content, expected_hash):
            result = original_update(content, expected_hash)
            self.backend.page['content']['raw'] += '<p>Human edit before readback.</p>'
            return result

        with patch.object(self.backend, 'update', side_effect=update_then_edit):
            with self.assertRaisesRegex(RuntimeError, 'written but readback differs'):
                apply_plan(self.plan(), self.backend)
        receipt = json.loads((self.bundle / 'private/publish-receipt.json').read_text())
        with self.assertRaisesRegex(ValueError, 'no verified post-update state'):
            restore_backup(receipt['backup'], self.backend)
        self.assertIn('Human edit before readback', page_text(self.backend.page))

    def test_corrupted_or_escaping_asset_stops(self):
        asset = self.prepared['assets'][0]
        (self.bundle / asset['path']).write_text('changed bytes')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            load_prepared(self.bundle)
        asset['path'] = '../outside.webp'
        write_json(self.bundle / 'prepared.json', self.prepared)
        with self.assertRaisesRegex(ValueError, 'leaves'):
            load_prepared(self.bundle)

    def test_changed_bundle_requires_new_plan(self):
        path = self.plan()
        self.prepared['config']['maps'][0]['title'] = 'New title after review'
        write_json(self.bundle / 'prepared.json', self.prepared)
        with self.assertRaisesRegex(ValueError, 'changed since planning'):
            apply_plan(path, self.backend)
        self.assertEqual(self.backend.uploads, 0)

    def test_rest_auth_stays_out_of_url_and_redirects_are_disabled(self):
        with patch.dict('os.environ', {'WP_USERNAME': 'fixture-user', 'WP_APPLICATION_PASSWORD': 'fixture-secret'}):
            client = RestBackend(self.config)
        with patch.object(client.session, 'request') as request:
            request.return_value.ok = True
            request.return_value.is_redirect = False
            request.return_value.json.return_value = self.page
            self.assertEqual(client.get_page(), self.page)
            args, kwargs = request.call_args
            self.assertNotIn('fixture-secret', args[1])
            self.assertFalse(kwargs['allow_redirects'])
            self.assertEqual(kwargs['params'], {'context': 'edit'})

    def test_wp_cli_payload_is_stdin_and_path_is_shell_quoted(self):
        client = WpCliBackend(self.config, 'website', '/srv/wordpress site')
        with patch('setouchi_futures_publish.subprocess.run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(self.page)
            self.assertEqual(client.get_page(), self.page)
            args, kwargs = run.call_args
            self.assertIn("'--path=/srv/wordpress site'", args[0][-1])
            self.assertEqual(json.loads(kwargs['input'])['op'], 'get_page')
            self.assertEqual(args[0][:4], ['ssh', '-o', 'BatchMode=yes', 'website'])

    def test_wp_cli_helper_has_valid_php_syntax(self):
        path = self.bundle / 'helper.php'
        path.write_text('<?php\n' + (ROOT / 'scripts/setouchi_futures_wp.php').read_text())
        result = subprocess.run(['php', '-l', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
