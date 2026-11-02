#!/usr/bin/env python3
"""Generate local wordlists; never sends requests or reads target files."""
import argparse
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]


def normalize(path):
    return path.strip().replace('\\', '/').rstrip('/')


def generate(categories=None, drives=('c',), usernames=(), extra_roots=(), separator='/'):
    catalog = json.loads((REPO / 'data/catalog.json').read_text())
    groups = {group['name']: group for group in catalog['groups']}
    if len(groups) != len(catalog['groups']) or 'legacy' in groups:
        raise ValueError('Catalog category names must be unique and cannot be legacy')
    for group in groups.values():
        if not group['roots'] or not group['files']:
            raise ValueError('Catalog groups must have roots and files')
        for root in group['roots']:
            if root != '{profile}' and not re.fullmatch(r'[a-zA-Z]:/[^\r\n{}]*', root + '/' if len(root) == 2 else root):
                raise ValueError('Invalid catalog root: ' + root)
        for file in group['files']:
            if (not file or file != file.strip() or file.startswith('/')
                    or any(char in file for char in '\\:\r\n{}')
                    or any(part in ('.', '..', '') for part in file.split('/'))):
                raise ValueError('Invalid relative catalog filename: ' + file)
    selected = set(categories or [*groups, 'legacy'])
    unknown = selected - (set(groups) | {'legacy'})
    if unknown:
        raise ValueError('Unknown categories: ' + ', '.join(sorted(unknown)))
    roots = {name: list(group['roots']) for name, group in groups.items()}
    for spec in extra_roots:
        name, delim, root = spec.partition('=')
        if not delim or name not in groups or not re.match(r'^[a-zA-Z]:[/\\]', root):
            raise ValueError('--root requires CATEGORY=absolute-drive-path')
        roots[name].append(normalize(root))
    drives = tuple(drive.rstrip(':').lower() for drive in drives)
    if not all(re.fullmatch('[a-z]', drive) for drive in drives):
        raise ValueError('Drive letters must be A through Z')
    profiles = ['c:/users/administrator', 'c:/users/default', 'c:/users/public',
                'c:/documents and settings/administrator',
                'c:/windows/system32/config/systemprofile',
                'c:/windows/serviceprofiles/localservice',
                'c:/windows/serviceprofiles/networkservice']
    for user in usernames:
        if not user or any(char in user for char in '/\\:\r\n') or user in ('.', '..'):
            raise ValueError('Usernames must be single path components')
        profiles.extend(['c:/users/' + user, 'c:/documents and settings/' + user])
    candidates = []
    if 'legacy' in selected:
        candidates.extend((REPO / 'data/legacy-paths.txt').read_text().splitlines())
        # Reuse every observed Administrator-relative path for supplied users.
        for path in list(candidates):
            for prefix in ('c:/users/administrator/', 'c:/documents and settings/administrator/'):
                if path.startswith(prefix):
                    for user in usernames:
                        candidates.append(prefix.replace('administrator', user) + path[len(prefix):])
    for name in sorted(selected - {'legacy'}):
        for root in roots[name]:
            for expanded in profiles if root == '{profile}' else [root]:
                candidates.extend(normalize(expanded) + '/' + file for file in groups[name]['files'])
    output = set()
    for candidate in candidates:
        path = normalize(candidate)
        if not path or '\n' in path or '\r' in path:
            raise ValueError('Invalid path in catalog')
        variants = [drive + path[1:] for drive in drives] if path[:3].lower() == 'c:/' else [path]
        for variant in variants:
            output.add(variant.replace('/', separator))
    return sorted(output, key=lambda value: (value.casefold(), value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--category', action='append', help='Repeat to select categories; default: all, including legacy')
    parser.add_argument('--drive', action='append', help='Repeat for drive letters; default: c')
    parser.add_argument('--username', action='append', default=[], help='Add a known username; repeatable')
    parser.add_argument('--root', action='append', default=[], help='Add CATEGORY=C:/custom/root; repeatable')
    parser.add_argument('--separator', choices=('forward', 'backslash'), default='forward')
    parser.add_argument('--list-categories', action='store_true')
    parser.add_argument('--output', type=Path, help='Default: stdout')
    args = parser.parse_args()
    if args.list_categories:
        print('legacy')
        print('\n'.join(group['name'] for group in json.loads((REPO / 'data/catalog.json').read_text())['groups']))
        return
    try:
        paths = generate(args.category, args.drive or ['c'], args.username, args.root,
                         '\\' if args.separator == 'backslash' else '/')
    except ValueError as error:
        parser.error(str(error))
    content = '\n'.join(paths) + '\n'
    if args.output:
        args.output.write_text(content, encoding='utf-8')
    else:
        sys.stdout.write(content)


if __name__ == '__main__':
    main()
