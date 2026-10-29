#!/usr/bin/env python3
"""Fails when any <text> in a served SVG variant renders below 12 px.

Usage: python3 tools/editorial/check_text_size.py   (stdlib only; reads assets/editorial and assets/agents)

Rendered size = font-size x (rendered width / viewBox width). An <img> is shrunk to its column by
max-width:100% and never enlarged, so rendered width = min(viewBox width, column). The *-desk-* files
are checked at columns 846, 700 and 563, the *-phone-* files at 308, the *-all-* files at 846.
In assets/agents the diagram's row images are drawn at a percentage of the column (node-*-desk-* 13.7%, conn-* 3.25%),
the step summaries (*-sum-*) at 94%, and the two empty-*.svg placeholders hold no text.
The SVG's own `@media (max-width: Npx)` rules see the rendered width, so they are applied before measuring.
A file that matches no kind, or a section below that is missing, fails too, so a new SVG cannot slip past unmeasured.
Only the rule shape the generator writes is understood: @media (max-width: Npx){.cls{prop:value;...}}.
"""
import glob, os, re, sys
import xml.etree.ElementTree as ET

MIN_PX = 12
COLUMNS = {'desk': (846, 700, 563), 'phone': (308,), 'all': (846,)}
# Accepted failures, each with its reason. Anything else below MIN_PX fails the check.
KNOWN = {}
# Every section the README embeds: name -> kinds. avatar.svg is the upload source for avatar.png, not a README image.
SECTIONS = {n: ('desk', 'phone') for n in ('masthead', 'about', 'focus', 'setup', 'principles', 'run', 'colophon')}
SECTIONS['say-hi'] = ('all',)
NOT_SERVED = {'avatar.svg'}
THEMES = ('light', 'dark')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, 'assets', 'editorial')
AGENTS = os.path.join(ROOT, 'assets', 'agents')
STEPS = ('you', 'orchestrator', 'workers', 'self-review', 'cross-model-review', 'done')
NODE_PCT, CONN_PCT, SUM_PCT = 13.7, 3.25, 94
# assets/agents file -> the columns it is checked at. A row image is NODE_PCT / CONN_PCT of the README column.
AGENT_FILES = {'empty.svg': (), 'empty-row.svg': ()}
for _theme in THEMES:
    for _kind in ('desk', 'phone'):
        AGENT_FILES[f'label-{_kind}-{_theme}.svg'] = COLUMNS[_kind]
    for _i, _slug in enumerate(STEPS):
        AGENT_FILES[f'node-{_slug}-desk-{_theme}.svg'] = tuple(c * NODE_PCT / 100 for c in COLUMNS['desk'])
        AGENT_FILES[f'node-{_slug}-phone-{_theme}.svg'] = COLUMNS['phone']
        for _kind in ('desk', 'phone'):
            AGENT_FILES[f'{_slug}-text-{_kind}-{_theme}.svg'] = COLUMNS[_kind]
            AGENT_FILES[f'{_slug}-visual-{_kind}-{_theme}.svg'] = COLUMNS[_kind]
            AGENT_FILES[f'{_slug}-sum-{_kind}-{_theme}.svg'] = tuple(c * SUM_PCT / 100 for c in COLUMNS[_kind])
        if _i < len(STEPS) - 1:
            AGENT_FILES[f'conn-{_i + 1}-desk-{_theme}.svg'] = tuple(c * CONN_PCT / 100 for c in COLUMNS['desk'])
MEDIA = re.compile(r'@media\s*\(\s*max-width:\s*([\d.]+)px\s*\)\s*\{\s*\.(\w+)\s*\{([^}]*)\}\s*\}')


def font_sizes(path, column):
    """Yield (text, rendered px) for every <text> of the SVG when shown in `column` px."""
    root = ET.parse(path).getroot()
    vw = float((root.get('viewBox') or '').split()[2])
    rendered_w = min(vw, column)
    css = ''.join(e.text or '' for e in root.iter('{http://www.w3.org/2000/svg}style'))
    rules = [(float(m[0]), m[1], dict(p.split(':') for p in m[2].split(';') if p)) for m in MEDIA.findall(css)]
    for t in root.iter('{http://www.w3.org/2000/svg}text'):
        size = float(t.get('font-size') or 0)
        for limit, cls, props in rules:
            if rendered_w <= limit and cls in (t.get('class') or '').split() and 'font-size' in props:
                size = float(props['font-size'].replace('px', ''))
        yield ''.join(t.itertext()), size * rendered_w / vw


def expected_files():
    """(directory, name) -> columns, for every SVG that must exist."""
    out = {}
    for sec, kinds in SECTIONS.items():
        for kind in kinds:
            for theme in THEMES:
                out[(ASSETS, f'{sec}-{kind}-{theme}.svg')] = COLUMNS[kind]
    out.update({(AGENTS, name): cols for name, cols in AGENT_FILES.items()})
    return out


def main():
    failed = known = checked = 0
    expected = expected_files()
    found = set()
    for directory in (ASSETS, AGENTS):
        found |= {(directory, os.path.basename(p)) for p in glob.glob(os.path.join(directory, '*.svg'))
                  if os.path.basename(p) not in NOT_SERVED}
    for directory, name in sorted(found ^ set(expected)):
        shown = os.path.join(os.path.relpath(directory, ROOT), name)
        print(f'FAIL {shown} {"is not a known section variant" if (directory, name) in found else "is missing"}')
        failed += 1
    for directory, name in sorted(found & set(expected)):
        path = os.path.join(directory, name)
        for col in expected[(directory, name)]:
            for text, px in font_sizes(path, col):
                checked += 1
                if px >= MIN_PX - 1e-6:
                    continue
                reason = KNOWN.get((name, col, text))
                print(f'{"KNOWN" if reason else "FAIL "} {name} col={col:g} {text[:24]!r} renders {px:.1f}px < {MIN_PX}px'
                      + (f' ({reason})' if reason else ''))
                known += bool(reason)
                failed += not reason
    print(f'{checked} text measurements, {failed} failing, {known} known')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
