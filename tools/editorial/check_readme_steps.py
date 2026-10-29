#!/usr/bin/env python3
"""Fails when the "How I run agents" steps in README.md are not six closed <details>, in order, that open in place.

Usage: python3 tools/editorial/check_readme_steps.py [repo root]   (stdlib only)

README.md must hold exactly six <details> blocks, closed by default. Each has one <summary> whose image alt starts
with "<n> <step name>", in the order You, Orchestrator, Workers, Self-review, Cross-model review, Done. Each body holds
the step's animated visual (assets/agents/<slug>-visual-*). Every image they reference (src and srcset) must exist,
and nothing in the README may link to docs/agents/, since the steps no longer have pages of their own.
"""
import os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STEPS = (('you', 'You'), ('orchestrator', 'Orchestrator'), ('workers', 'Workers'), ('self-review', 'Self-review'),
         ('cross-model-review', 'Cross-model review'), ('done', 'Done'))


class Blocks(HTMLParser):
    """Collects each <details>: whether it is open, the images in its <summary> and in its body, and every href."""
    def __init__(self):
        super().__init__()
        self.blocks, self.hrefs, self.errors, self.depth, self.in_summary = [], [], [], 0, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.hrefs.append(a['href'])
        if tag == 'details':
            if self.depth:
                self.errors.append(f'<details> number {len(self.blocks) + 1} is nested inside another <details>, the steps must be separate top-level blocks')
            self.depth += 1
            self.blocks.append({'open': 'open' in a, 'summaries': 0, 'summary_imgs': [], 'body_imgs': [], 'files': []})
        elif tag == 'summary' and self.blocks and self.depth:
            self.in_summary = True
            self.blocks[-1]['summaries'] += 1
        elif tag in ('img', 'source') and self.blocks and self.depth:
            b = self.blocks[-1]
            for url in ([a['src']] if a.get('src') else []) + re.findall(r'[^\s,]+', a.get('srcset') or ''):
                b['files'].append(url)
            if tag == 'img':
                b['summary_imgs' if self.in_summary else 'body_imgs'].append(a.get('alt') or '')

    def handle_endtag(self, tag):
        if tag == 'summary':
            self.in_summary = False
        elif tag == 'details':
            if self.depth:
                self.depth -= 1
            else:
                self.errors.append('unmatched </details> with no open <details>')


def main(root):
    failed = 0

    def fail(msg):
        nonlocal failed
        print('FAIL ' + msg)
        failed += 1

    parser = Blocks()
    parser.feed(open(os.path.join(root, 'README.md')).read())
    for err in parser.errors:
        fail('README.md has ' + err)
    if parser.depth:
        fail(f'README.md ends with {parser.depth} <details> still open, every <details> needs its </details>')
    for href in parser.hrefs:
        if 'docs/agents/' in href:
            fail(f'README.md links {href}; the steps open in place, with no page of their own')
    if len(parser.blocks) != len(STEPS):
        fail(f'README.md has {len(parser.blocks)} <details> blocks, it must have {len(STEPS)}')
    images = 0
    for i, ((slug, title), b) in enumerate(zip(STEPS, parser.blocks), 1):
        if b['open']:
            fail(f'step {i} ({title}) is open by default, it must start closed')
        if b['summaries'] != 1:
            fail(f'step {i} ({title}) has {b["summaries"]} <summary> elements, it must have 1')
        alts = b['summary_imgs']
        if not alts or not alts[0].startswith(f'{i} {title}'):
            fail(f'step {i}: the <summary> image alt must start with "{i} {title}", it is {alts[:1]}')
        if not any(f'assets/agents/{slug}-visual-' in f for f in b['files']):
            fail(f'step {i} ({title}) does not show assets/agents/{slug}-visual-*')
        for url in b['files']:
            images += 1
            if not os.path.isfile(os.path.join(root, url)):
                fail(f'step {i} ({title}): {url} does not exist')
    print(f'{len(parser.blocks)} <details> blocks, {images} image files referenced, {failed} failing')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ROOT))
