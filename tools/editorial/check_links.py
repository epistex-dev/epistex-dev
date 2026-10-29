#!/usr/bin/env python3
"""Fails when a link or image in README.md points at a file that is not in the repo.

Usage: python3 tools/editorial/check_links.py [repo root]   (stdlib only)

Every href, src and srcset URL is checked: a relative one must resolve to an existing file (relative to the
Markdown file that holds it), an absolute one must be in ALLOWED, so a rename or a missing image fails here instead
of on github.com.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALLOWED = {'https://github.com/epistex-dev', 'mailto:epistex.dev@gmail.com'}
ATTR = re.compile(r'\b(?:href|src|srcset)="([^"]*)"')


def main(root):
    failed = checked = 0
    pages = [os.path.join(root, 'README.md')]
    for page in pages:
        rel_page = os.path.relpath(page, root)
        for url in ATTR.findall(open(page).read()):
            checked += 1
            if re.match(r'[a-z][a-z0-9+.-]*:', url):
                if url not in ALLOWED:
                    print(f'FAIL {rel_page}: {url} is not an allowed absolute URL')
                    failed += 1
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(page), url.split('#')[0]))
            if not os.path.isfile(target) or not target.startswith(os.path.abspath(root) + os.sep):
                print(f'FAIL {rel_page}: {url} does not resolve to a file in the repo')
                failed += 1
    print(f'{checked} links and images in {len(pages)} files, {failed} failing')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ROOT))
