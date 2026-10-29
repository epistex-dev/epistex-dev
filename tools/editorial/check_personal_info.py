#!/usr/bin/env python3
"""Fails when the employer, the city or the real name appears in README.md, tools/ or assets/.

Usage: python3 tools/editorial/check_personal_info.py   (stdlib only)

Matching is case-insensitive on NFC-normalised text. Embedded font data is dropped first, since base64 can spell
anything by chance. The terms are written as regexes with one character in a class, so this file does not match itself.
"""
import os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TERMS = re.compile(r'AIDI[A]|Hano[i]|H[à]\s*N[ộ]i|Ng[ọ]c|Ngo[c]', re.I)
FONT_DATA = re.compile(r'data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+')
SKIP_SUFFIX = ('.png', '.pyc')


def files():
    yield os.path.join(ROOT, 'README.md')
    for top in ('tools', 'assets'):
        for dirpath, dirs, names in os.walk(os.path.join(ROOT, top)):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for n in sorted(names):
                if not n.endswith(SKIP_SUFFIX):
                    yield os.path.join(dirpath, n)


def main():
    hits = scanned = 0
    for path in files():
        scanned += 1
        text = unicodedata.normalize('NFC', FONT_DATA.sub('', open(path, encoding='utf-8', errors='replace').read()))
        for no, line in enumerate(text.splitlines(), 1):
            for m in TERMS.finditer(line):
                hits += 1
                print(f'FAIL {os.path.relpath(path, ROOT)}:{no} {m.group(0)!r} in ...{line[max(0, m.start() - 30):m.end() + 30]}...')
    print(f'{scanned} files scanned, {hits} personal-info matches')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
