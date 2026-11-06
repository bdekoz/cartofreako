#!/usr/bin/env python3
"""Prepare the Setouchi galleries locally, then plan/verify explicit WordPress updates."""
import argparse
import json
from pathlib import Path
import sys
import requests

from setouchi_futures import DEFAULT_MANIFEST, ROOT, load_config, prepare
from setouchi_futures_publish import (RestBackend, WpCliBackend, apply_plan, load_prepared,
                                      make_plan, restore_backup, verify_receipt)


def backend(args, config, transport):
    if transport == 'wp-cli':
        return WpCliBackend(config, args.ssh_host, args.wp_path)
    return RestBackend(config, args.credentials_file)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare', help='Build local images, preview, blocks, and unsent outreach brief')
    prep.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    prep.add_argument('--output', type=Path)
    prep.add_argument('--workers', type=int, default=2)
    prep.add_argument('--hamonshu-root', type=Path)
    prep.add_argument('--download-sources', action='store_true')
    for command in ('plan', 'apply', 'verify', 'restore'):
        p = commands.add_parser(command)
        p.add_argument('--credentials-file', type=Path)
        p.add_argument('--ssh-host')
        p.add_argument('--wp-path')
        if command == 'plan':
            p.add_argument('--bundle', type=Path, default=ROOT / load_config()['output'])
            p.add_argument('--page-id', type=int, default=3175)
            p.add_argument('--transport', choices=['rest', 'wp-cli'], default='rest')
            p.add_argument('--page-file', type=Path, help='Read an exported context=edit page; no remote connection')
        elif command == 'apply':
            p.add_argument('--plan', type=Path, required=True)
        elif command == 'verify':
            p.add_argument('--receipt', type=Path, required=True)
            p.add_argument('--public', action='store_true', help='Also check public page and media URLs')
        else:
            p.add_argument('--backup', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            if not 1 <= args.workers <= 8:
                raise ValueError('--workers must be between 1 and 8')
            output, prepared = prepare(args.manifest, args.output, args.workers, args.hamonshu_root, args.download_sources)
            print(json.dumps({'output': str(output), 'media_assets': len(prepared['assets']), 'status': 'local-only'}))
        elif args.command == 'plan':
            prepared = load_prepared(args.bundle)
            if args.page_id != prepared['config']['page_id']:
                raise ValueError('--page-id differs from the approved manifest')
            page = json.loads(args.page_file.read_text()) if args.page_file else backend(args, prepared['config'], args.transport).get_page()
            path, plan = make_plan(args.bundle, page, args.transport, bool(args.page_file))
            print(json.dumps({'plan': str(path), 'media_assets': len(plan['media_keys']), 'remote_writes': 0}))
        elif args.command == 'apply':
            plan = json.loads(args.plan.read_text())
            config = load_prepared(plan['bundle'])['config']
            path, receipt = apply_plan(args.plan, backend(args, config, plan['transport']))
            print(json.dumps({'receipt': str(path), 'status': receipt['status'], 'page_changed': receipt['page_changed']}))
        elif args.command == 'verify':
            receipt = json.loads(args.receipt.read_text())
            print(json.dumps(verify_receipt(args.receipt, backend(args, receipt['config'], receipt['transport']), args.public)))
        else:
            saved = json.loads(args.backup.read_text())
            print(json.dumps(restore_backup(args.backup, backend(args, saved['config'], saved['transport']))))
    except requests.RequestException:
        print('Error: WordPress network request failed; no credentials or response body logged', file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
