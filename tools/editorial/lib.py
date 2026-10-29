#!/usr/bin/env python3
"""Shared helpers for the Epistex profile generator: font subsetting, SVG text layout, <picture> markup.

Needs fontTools + brotli, and @fontsource/{overpass,newsreader,hanken-grotesk,ibm-plex-sans,ibm-plex-mono}
unpacked under $FONTSOURCE (its node_modules/@fontsource).
"""
import base64, collections, html, io, math, os, re
from fontTools.ttLib import TTFont
from fontTools import subset as ftsubset

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(os.path.dirname(HERE))
FONTSOURCE = os.environ['FONTSOURCE']

FONT_FILES = {}
for fam, prefix, keys in [
    ('overpass', 'ov', ['400', '600', '700', '800']),
    ('newsreader', 'nr', ['400', '400i', '500', '600', '700i']),
    ('hanken-grotesk', 'hk', ['500', '600']),
    ('ibm-plex-sans', 'px', ['400', '500', '600']),
    ('ibm-plex-mono', 'pm', ['400', '500']),
]:
    for k in keys:
        style = 'italic' if k.endswith('i') else 'normal'
        FONT_FILES[prefix + k] = f'{fam}/files/{fam}-latin-{k.rstrip("i")}-{style}.woff2'

# ---------------------------------------------------------------- content
ABOUT = ("I'm a software engineer working with AI agents. Most days I build the small tools around them "
         "(tests, reviews, helpers) so their work is easier to check.")
FOCUS = [
    ('Agents you can trust:', ' verification before delegation.'),
    ('Tool use beyond the API:', ' a Wayland desktop and a live browser as agent tools.'),
    ('Orchestration:', ' parent agents that hear every child.'),
    ('Evals:', ' judged A/B rounds, not vibes.'),
]
PRINCIPLES = ['Evidence over confidence.', 'Blocking means a reachable trigger.', 'Process over rule lists.',
              'AI knowledge and software engineering: two equal halves.']
# (key, [(text, 0 = the tool, 1 = its detail)]).
SETUP = [
    ('System', [('CachyOS', 0), (' \u00b7 Linux', 1)]),
    ('Desktop', [('niri', 0), (' \u00b7 Wayland', 1)]),
    ('Shell', [('fish', 0)]),
    ('Terminal', [('Ghostty', 0)]),
    ('Browser', [('Brave', 0)]),
    ('Hardware', [('Core i7-14700', 0), (' \u00b7 20 cores \u00b7 28 threads', 1)]),
    ('Agents', [('Claude Code', 0), (' \u00b7 Pi \u00b7 T3 Code', 1)]),
]
SETUP_ALT = 'Setup. ' + ' '.join(f'{k}: {"".join(t for t, _ in v).replace(" \u00b7 ", ", ")}.' for k, v in SETUP)
# The replayed run: (glyph, mono pieces, outcome). Glyphs are drawn, since Plex Mono's latin subset has no arrow or check.
RUN = [
    ('$', [('orchestrate', 'pm500', 'ink'), (' "add passkey login,', 'pm400', 'ink2'), (' keep passwords as fallback"', 'pm400', 'ink2')], None),
    ('>', [('split', 'pm500', 'ink'), ('4 briefs', 'pm400', 'ink2')], 'schema first'),
    ('>', [('worker', 'pm500', 'ink'), ('\u00d74', 'pm400', 'ink2')], 'in parallel, red then green'),
    ('>', [('review', 'pm500', 'ink'), ('cross-model', 'pm400', 'ink2')], '1 blocking: challenge replay'),
    ('>', [('fix', 'pm500', 'ink'), ('+ test', 'pm400', 'ink2')], 'replay rejected'),
    ('ok', [('done', 'pm500', 'acc'), (', with evidence', 'nr400i', 'acc')], None),
]
RUN_ALT = ('A run, replayed. $ orchestrate "add passkey login, keep passwords as fallback". Split: 4 briefs, schema first. '
           'Worker times 4: in parallel, red then green. Review: cross-model, 1 blocking: challenge replay. '
           'Fix: a test, replay rejected. Done, with evidence.')
# Seconds: first line, gap between lines, fade-in, hold of the full log, fade-out, blank before the loop.
RUN_FIRST, RUN_STEP, RUN_IN, RUN_HOLD, RUN_OUT, RUN_BLANK = 0.4, 0.6, 0.3, 4.0, 0.5, 0.3
# Family names as embedded in the woff2 files (name table), for the colophon.
SERIF, MONO = 'Newsreader', 'IBM Plex Mono'
COLOPHON = ('Set in ', SERIF, ' & ', MONO, ' \u00b7 built by agents, reviewed across models.')
SAY_HI = 'Say hi'
TAGLINE_ALT = 'Epistex. Epistex: from episteme (knowledge) to execution.'
EMAIL_HREF = 'mailto:epistex.dev@gmail.com'

# ---------------------------------------------------------------- fonts
_metrics = {}


def metrics(key):
    if key not in _metrics:
        f = TTFont(os.path.join(FONTSOURCE, FONT_FILES[key]))
        _metrics[key] = (f.getBestCmap(), f['hmtx'].metrics, f['head'].unitsPerEm)
    return _metrics[key]


def width(text, key, size, ls=0):
    cmap, hm, upm = metrics(key)
    w = sum(hm[cmap[ord(c)]][0] if ord(c) in cmap else upm * 0.5 for c in text)
    return w * size / upm + ls * len(text)


_subset_cache = {}


def subset_b64(key, chars):
    ck = (key, chars)
    if ck not in _subset_cache:
        f = TTFont(os.path.join(FONTSOURCE, FONT_FILES[key]))
        opts = ftsubset.Options()
        opts.flavor = 'woff2'
        opts.layout_features = ['kern', 'liga', 'tnum']
        sub = ftsubset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = 'woff2'
        f.save(buf)
        _subset_cache[ck] = base64.b64encode(buf.getvalue()).decode()
    return _subset_cache[ck]


def esc(t):
    return html.escape(t, quote=True)


# ---------------------------------------------------------------- svg builder
class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.body, self.css = [], []
        self.used = collections.defaultdict(set)

    def add(self, *parts):
        self.body.extend(parts)

    def text(self, x, y, lines, size, lh=None, anchor='start', ls=0, cls=''):
        """lines: list of lines, each a list of (text, font, color) pieces."""
        lh = lh or size * 1.3
        for i, line in enumerate(lines):
            spans = []
            for t, f, c in line:
                self.used[f].update(t)
                spans.append(f'<tspan font-family="\'{f}\'" fill="{c}">{esc(t)}</tspan>')
            extra = f' letter-spacing="{ls}"' if ls else ''
            extra += f' class="{cls}"' if cls else ''
            self.add(f'<text x="{x:.1f}" y="{y + i * lh:.1f}" font-size="{size}" text-anchor="{anchor}"{extra}>{"".join(spans)}</text>')
        return y + (len(lines) - 1) * lh

    def render(self):
        faces = ''.join(
            f"@font-face{{font-family:'{k}';src:url(data:font/woff2;base64,{subset_b64(k, ''.join(sorted(v)))}) format('woff2')}}"
            for k, v in sorted(self.used.items()))
        h = int(round(self.h))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" viewBox="0 0 {self.w} {h}" role="img">'
                f'<title>{esc(self.title)}</title><style>{faces}text{{white-space:pre}}{"".join(self.css)}</style>'
                f'{"".join(self.body)}</svg>')


def wrap(segs, size, maxw, widths=None, ls=0):
    """Greedy wrap of (text, font, color) pieces; widths gives per-line max widths for the first lines."""
    words, cur = [], []
    for t, f, c in segs:
        for m in re.finditer(r'\S+|\s+', t):
            tok = m.group(0)
            if tok.isspace():
                if cur:
                    words.append((cur, (' ', f, c)))
                    cur = []
            else:
                cur.append((tok, f, c))
    if cur:
        words.append((cur, None))
    lines, line, lw = [], [], 0.0
    for core, sp in words:
        cw = sum(width(t, f, size, ls) for t, f, c in core)
        limit = widths[len(lines)] if widths and len(lines) < len(widths) else maxw
        if line and lw + cw > limit:
            while line and line[-1][0] == ' ':
                line.pop()
            lines.append(line)
            line, lw = [], 0.0
        line.extend(core)
        lw += cw
        if sp:
            line.append(sp)
            lw += width(' ', sp[1], size, ls)
    while line and line[-1][0] == ' ':
        line.pop()
    if line:
        lines.append(line)
    return [merge(l) for l in lines]


def merge(line):
    out = []
    for p in line:
        if out and out[-1][1:] == p[1:]:
            out[-1] = (out[-1][0] + p[0],) + p[1:]
        else:
            out.append(p)
    return out


def find_piece(lines, needle, size, ls=0):
    """(line index, x start, x end) of the piece containing needle."""
    for i, line in enumerate(lines):
        x = 0.0
        for t, f, c in line:
            if needle in t:
                pre = t[:t.index(needle)]
                x0 = x + width(pre, f, size, ls)
                return i, x0, x0 + width(needle, f, size, ls)
            x += width(t, f, size, ls)
    raise KeyError(needle)


D2 = {
    'light': dict(bg='#ffffff', ink='#141414', ink2='#474747', ink3='#6f6f6f', rule='#dadada', acc='#1d4ed8'),
    'dark': dict(bg='#0d1117', ink='#ececea', ink2='#b5b5b2', ink3='#8e8e8a', rule='#30363d', acc='#86a8ff'),
}


def label_steps(size, W, lo=563, ratio=1.06):
    """In-SVG @media rules that grow the strip labels as the image shrinks below W, so they render >= `size` px.

    An <img> shrinks with its column, and a media query inside the SVG sees the rendered width, which no
    page-level <source media> can know. Each step holds from its upper width down to the next one, where it
    renders exactly `size`; the label is at most `ratio` times larger in between.
    """
    edges = [W]
    while edges[-1] > lo:
        edges.append(max(lo, edges[-1] / ratio))
    rules = []
    for hi, low in zip(edges, edges[1:]):
        fs = math.ceil(size * W / low * 10) / 10
        rules.append(f'@media (max-width:{hi - 0.1:g}px){{.lab{{font-size:{fs:g}px}}}}')
    return ''.join(rules)


# ---------------------------------------------------------------- output helpers
WRITTEN = []


def save(rel, svg):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write(svg.render() if isinstance(svg, Svg) else svg)
    WRITTEN.append(rel)


def themed(rel_base, build, palettes, variants):
    """Write rel_base-<variant>-<theme>.svg for each variant ('desk', 'phone' or 'all')."""
    for v in variants:
        for theme, pal in palettes.items():
            save(f'{rel_base}-{v}-{theme}.svg', build(pal, v))


def pic(base, alt, kind='both', href=None, width=None, align=None):
    """GitHub-safe <picture>. kind: both (desktop and phone variants) | all (one size). width: percent of the column. align: the img align attribute."""
    a = esc(alt)
    w = (f' width="{width}%"' if width else '') + (f' align="{align}"' if align else '')
    if kind == 'all':
        h = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}-all-dark.svg">'
             f'<img src="{base}-all-light.svg"{w} alt="{a}"></picture>')
    else:
        h = (f'<picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="{base}-phone-dark.svg">'
             f'<source media="(max-width: 600px)" srcset="{base}-phone-light.svg">'
             f'<source media="(prefers-color-scheme: dark)" srcset="{base}-desk-dark.svg">'
             f'<img src="{base}-desk-light.svg"{w} alt="{a}"></picture>')
    return f'<a href="{esc(href)}">{h}</a>' if href else h
