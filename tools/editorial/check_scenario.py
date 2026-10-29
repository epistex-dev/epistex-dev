#!/usr/bin/env python3
"""Fails when the example scenario is not the passkey one: no old scenario left, the intent in the run log and the You step.

Usage: python3 tools/editorial/check_scenario.py [repo root]   (stdlib only)

README.md and every SVG under assets/ must not mention the old example ("flaky", "login retry", "session timeout",
"token refresh") or the old agent name ("Droid", replaced by "Pi"), in any case.
The Setup SVGs (assets/editorial/setup-*) and the Setup alt text in README.md must hold no version-like number (digits with a dot,
such as 4.9.3 or 26.04) and no kernel string ("Linux 7.x", "-cachyos"); hardware numbers (14700, 20, 28) are allowed. The intent "add passkey login" must be in README.md, in the run log (assets/editorial/run-*)
and in the You step (assets/agents/you-text-* and you-visual-*), judged by each SVG's <title>, which holds its full text.
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = ('flaky', 'login retry', 'session timeout', 'token refresh', 'droid')
VERSION = re.compile(r'\d+\.\d+|linux \d|\d-cachyos')
INTENT = 'add passkey login'
WITH_INTENT = ('assets/editorial/run-*.svg', 'assets/agents/you-text-*.svg', 'assets/agents/you-visual-*.svg')


def main(root):
    failed = 0

    def fail(msg):
        nonlocal failed
        print('FAIL ' + msg)
        failed += 1

    def read(path):
        return open(os.path.join(root, path), encoding='utf-8').read()

    files = ['README.md'] + sorted(os.path.relpath(f, root) for f in glob.glob(os.path.join(root, 'assets', '**', '*.svg'), recursive=True))
    for f in files:
        low = re.sub(r'\s+', ' ', read(f)).lower()
        for word in OLD:
            if word in low:
                fail(f'{f} still holds the old scenario: "{word}"')
    setup = [('README.md', m) for m in re.findall(r'alt="(Setup\.[^"]*)"', read('README.md'))]
    for path in sorted(glob.glob(os.path.join(root, 'assets/editorial/setup-*.svg'))):
        f = os.path.relpath(path, root)
        setup += [(f, t) for t in re.findall(r'>([^<>]+)<', read(f))]
    if len(setup) < 2:
        fail('no Setup text found to check for versions')
    for f, text in setup:
        found = VERSION.search(text.lower())
        if found:
            fail(f'{f} holds a version in the Setup text: "{found.group(0)}" in "{text[:60]}"')
    if INTENT not in read('README.md').lower():
        fail(f'README.md does not hold the intent "{INTENT}"')
    checked = 0
    for pattern in WITH_INTENT:
        found = sorted(glob.glob(os.path.join(root, pattern)))
        if not found:
            fail(f'no file matches {pattern}')
        for path in found:
            f = os.path.relpath(path, root)
            title = re.search(r'<title>(.*?)</title>', read(f), re.S)
            checked += 1
            if not title or INTENT not in title.group(1).lower():
                fail(f'{f} does not hold the intent "{INTENT}" in its <title>')
    print(f'{len(files)} files scanned for the old scenario, {checked} files checked for the intent, {failed} failing')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ROOT))
