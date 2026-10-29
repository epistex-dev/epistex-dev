#!/usr/bin/env python3
"""Fails when a step label in the diagram has a dotted underline: the labels are not links, so no <line> with a dash pattern
may sit in assets/agents/node-*.svg.

Usage: python3 tools/editorial/check_no_underline.py [repo root]   (stdlib only)
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UNDERLINE = re.compile(r'<line\b[^>]*\bstroke-dasharray=')


def main(root):
    files = sorted(glob.glob(os.path.join(root, 'assets/agents/node-*.svg')))
    failed = 0
    if not files:
        print('FAIL no assets/agents/node-*.svg found')
        return 1
    for path in files:
        with open(path, encoding='utf-8') as fh:
            if UNDERLINE.search(fh.read()):
                print(f'FAIL {os.path.relpath(path, root)} has a dotted underline under its label')
                failed += 1
    print(f'{len(files)} node files checked for a dotted underline, {failed} failing')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ROOT))
