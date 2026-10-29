#!/usr/bin/env python3
"""Regenerates assets/editorial/*.svg, assets/agents/*.svg and README.md of the epistex-dev profile
(Editorial design, AI-engineering role). The "How I run agents" section (diagram and six steps that open in place) comes from agents.py.

Usage, from anywhere:
  pip install fonttools brotli
  npm i --prefix "$FONTSOURCE" @fontsource/{overpass,newsreader,hanken-grotesk,ibm-plex-sans,ibm-plex-mono}
  FONTSOURCE=$FONTSOURCE/node_modules/@fontsource python3 tools/editorial/build.py
Edit text in lib.py (profile) or agents.py (the steps).
Then check: python3 tools/editorial/check_text_size.py; python3 tools/editorial/check_links.py; python3 tools/editorial/check_readme_steps.py; python3 tools/editorial/check_personal_info.py; python3 tools/editorial/check_no_underline.py
assets/editorial/avatar.png (for a manual upload) is rendered from avatar.svg:
  brave --headless --window-size=460,460 --screenshot=assets/editorial/avatar.png file://$PWD/assets/editorial/avatar.svg
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import agents


def tag2(p):
    return [('Epistex: from ', 'nr400i', p['ink2']), ('episteme', 'nr700i', p['ink']), (' (knowledge) to ', 'nr400i', p['ink2']),
            ('execution', 'nr700i', p['ink']), ('.', 'nr400i', p['ink2'])]


# Desk SVGs shrink to 563 px at a 1012 px window, so their text must be >= 12 * 846 / 563 = 18.03 px.
DESK_MIN = 18.5


def d2_about(p, v):
    """The About copy with a drop cap."""
    s, phone, x, cw, y0 = d2_side_section(p, v, 'About', f'About. {ABOUT}')
    size, lh = (18, 28) if phone else (21, 33)
    cap_size = round((lh + size * 0.68) / 0.68)
    s.text(x - 2, y0 + lh, [[(ABOUT[0], 'nr500', p['ink'])]], cap_size)
    capw = width(ABOUT[0], 'nr500', cap_size) + 8
    # The first line hugs the cap to keep the opening word whole ("I'm").
    first = capw - 9
    lines = wrap([(ABOUT[1:], 'nr400', p['ink'])], size, cw, widths=[cw - first, cw - capw])
    for i, line in enumerate(lines):
        s.text(x + ((first if i == 0 else capw) if i < 2 else 0), y0 + i * lh, [line], size)
    s.h = y0 + (len(lines) - 1) * lh + (40 if not phone else 32)
    return s


def d2_side_section(p, v, label, alt):
    """The About layout: label in a 220 px left column on desk, above the content on phone."""
    phone = v == 'phone'
    W = 308 if phone else 846
    s = Svg(W, 0, alt)
    s.add(f'<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{p["rule"]}"/>')
    if not phone:
        s.text(0, 44, [[(label, 'nr400i', p['acc'])]], 20)
        return s, phone, 220, 626, 44
    s.text(0, 34, [[(label, 'nr400i', p['acc'])]], 18)
    return s, phone, 0, 308, 72


def d2_focus(p, v):
    alt = 'Focus. ' + ' '.join(f'{i + 1}. {a}{b}' for i, (a, b) in enumerate(FOCUS))
    s, phone, x, cw, y = d2_side_section(p, v, 'Focus', alt)
    size, lh, gap, ind = (18, 27, 14, 22) if phone else (21, 31, 16, 30)
    end = y
    for i, (lead, rest) in enumerate(FOCUS):
        s.text(x, y, [[(f'{i + 1}', 'nr400i', p['ink3'])]], size)
        end = s.text(x + ind, y, wrap([(lead, 'nr600', p['ink']), (rest, 'nr400', p['ink2'])], size, cw - ind), size, lh=lh)
        y = end + lh + gap
    s.h = end + (32 if phone else 40)
    return s


def d2_setup(p, v):
    """A spec sheet: italic keys, the tool's name in ink and its detail in ink2, a hairline between rows."""
    s, phone, x, cw, y = d2_side_section(p, v, 'Setup', SETUP_ALT)
    ks, vs, kw, lh, below, above = (16, 17, 88, 24, 13, 27) if phone else (DESK_MIN, 21, 132, 30, 15, 33)
    for i, (key, val) in enumerate(SETUP):
        s.text(x, y, [[(key, 'nr400i', p['ink3'])]], ks)
        # Wrap whole items, never inside one: "20 cores" must not lose its "20".
        items = [(part, 'nr500' if dim == 0 else 'nr400', p['ink'] if dim == 0 else p['ink2'])
                 for t, dim in val for part in t.split(' \u00b7 ') if part]
        sep = (' \u00b7 ', 'nr400', p['ink2'])
        lines, cur, lw = [], [], 0.0
        for item in items:
            add = width(item[0], item[1], vs) + (width(sep[0], sep[1], vs) if cur else 0)
            if cur and lw + add > cw - kw:
                lines.append(cur)
                cur, lw, add = [], 0.0, width(item[0], item[1], vs)
            cur += ([sep] if cur else []) + [item]
            lw += add
        lines.append(cur)
        end = s.text(x + kw, y, lines, vs, lh=lh)
        if i < len(SETUP) - 1:
            s.add(f'<line x1="{x}" y1="{end + below + .5:.1f}" x2="{x + cw}" y2="{end + below + .5:.1f}" stroke="{p["rule"]}"/>')
            y = end + below + above
    s.h = end + (32 if phone else 40)
    return s


def pencil(s, x0, x1, y, p):
    """The underline with its drawn stroke as the static state: only the running animation hides it, so a frame
    taken before or without the animation still shows the underline."""
    L = (x1 - x0) * 1.1 + 20
    s.css.append(f'.pen{{stroke-dasharray:{L:.0f};animation:draw .9s .3s cubic-bezier(.23,1,.32,1) backwards}}'
                 f'@keyframes draw{{from{{stroke-dashoffset:{L:.0f}}}to{{stroke-dashoffset:0}}}}'
                 '@media (prefers-reduced-motion: reduce){.pen{animation:none}}')
    s.add(f'<path class="pen" d="M{x0 - 3:.1f} {y + 1:.1f}Q{(x0 + x1) / 2:.1f} {y - 3:.1f} {x1 + 6:.1f} {y - 1:.1f}" fill="none" '
          f'stroke="{p["acc"]}" stroke-width="2.6" stroke-linecap="round"/>')


def d2_masthead(p, v):
    phone = v == 'phone'
    W = 308 if phone else 846
    s = Svg(W, 0, TAGLINE_ALT)
    fs = 12
    lab = '' if phone else 'lab'
    if lab:
        s.css.append('.trk{letter-spacing:.1em}' + label_steps(fs, W))
    s.add(f'<line x1="0" y1="1" x2="{W}" y2="1" stroke="{p["ink"]}" stroke-width="2"/>')
    s.text(0, 26, [[('epistex-dev', 'hk600', p['ink3'])]], fs, ls=1.2, cls=f'{lab} trk' if lab else '')
    s.text(W, 26, [[('software engineer', 'hk500', p['ink3'])]], fs, anchor='end', cls=lab)
    s.add(f'<line x1="0" y1="40.5" x2="{W}" y2="40.5" stroke="{p["rule"]}"/>')
    if not phone:
        s.text(-8, 200, [[('Epistex', 'nr500', p['ink'])]], 172, ls=-6)
        size, y0, lines = 28, 272, [tag2(p)]
    else:
        s.text(-4, 128, [[('Epistex', 'nr500', p['ink'])]], 92, ls=-3)
        size, y0 = 20, 172
        lines = wrap(tag2(p), size, W)
    lh = size * 1.35
    end = s.text(0, y0, lines, size, lh=lh)
    i, x0, x1 = find_piece(lines, 'execution', size)
    pencil(s, x0, x1, y0 + i * lh + 9, p)
    s.h = end + 30
    return s


def run_glyph(kind, x, y, size, p):
    """The row's lead: '$' as text, an arrow or a check drawn at the x-height of a size-px mono line."""
    k, mid = size / 20, y - size * 0.3
    if kind == '>':
        return (f'<path d="M{x:.1f} {mid:.1f}H{x + 15 * k:.1f}M{x + 10 * k:.1f} {mid - 4.5 * k:.1f}L{x + 15 * k:.1f} {mid:.1f}'
                f'L{x + 10 * k:.1f} {mid + 4.5 * k:.1f}" fill="none" stroke="{p["ink3"]}" stroke-width="1.4" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    return (f'<path d="M{x + 1 * k:.1f} {mid:.1f}L{x + 5.5 * k:.1f} {mid + 4.5 * k:.1f}L{x + 15 * k:.1f} {mid - 6 * k:.1f}" '
            f'fill="none" stroke="{p["acc"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


def d2_run(p, v):
    """A3's replayed agent run: the log types itself in line by line, holds, fades and loops.

    The static state is the complete log; only the running animation hides lines, and reduced motion stops it.
    """
    phone = v == 'phone'
    W = 308 if phone else 846
    s = Svg(W, 0, RUN_ALT)
    s.add(f'<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{p["rule"]}"/>')
    s.text(0, 42, [[('A run, replayed', 'nr400i', p['acc'])]], 18 if phone else 20)
    ms, ss, lh, y = (14, 15, 27, 92) if phone else (22, 23.5, 44, 112)
    ch = ms * 0.6
    x_lead, x_step = 3 * ch, 3 * ch + (7.5 if phone else 8) * ch
    sep = (' \u00b7 ', 'pm400', p['ink3'])
    n = len(RUN)
    hold = RUN_FIRST + RUN_STEP * (n - 1) + RUN_IN + RUN_HOLD
    T = hold + RUN_OUT + RUN_BLANK
    pc = lambda t: f'{t / T * 100:.2f}%'
    ease = 'animation-timing-function:cubic-bezier(.23,1,.32,1)'
    for i, (glyph, pieces, outcome) in enumerate(RUN):
        a = RUN_FIRST + RUN_STEP * i
        s.css.append(f'.r{i}{{animation:k{i} {T:g}s linear infinite}}'
                     f'@keyframes k{i}{{0%,{pc(a)}{{opacity:0;transform:translateY(6px);{ease}}}'
                     f'{pc(a + RUN_IN)},{pc(hold)}{{opacity:1;transform:none}}{pc(hold + RUN_OUT)},100%{{opacity:0;transform:none}}}}')
        s.add(f'<g class="r{i}">')
        pcs = [(t, f, p[c]) for t, f, c in pieces]
        if glyph == '$':
            s.text(0, y, [[('$', 'pm400', p['ink3'])]], ms)
            rows = [[(x_lead, pcs)]]
            if x_lead + sum(width(t, f, ms) for t, f, _ in pcs) > W:
                rows = [[(x_lead, [(t.lstrip(), f, c)])] for t, f, c in pcs]
        else:
            s.add(run_glyph(glyph, 0, y, ms, p))
            if outcome is None:
                rows = [[(x_lead, pcs)]]
            else:
                tail = [sep, (outcome, 'nr400i', p['ink2'])]
                rows = [[(x_lead, pcs[:1]), (x_step, pcs[1:] + tail)]]
                if x_step + sum(width(t, f, ss if f.startswith('nr') else ms) for t, f, _ in pcs[1:] + tail) > W:
                    rows = [[(x_lead, pcs[:1]), (x_step, pcs[1:])], [(x_step, [(outcome, 'nr400i', p['ink2'])])]]
        for r, row in enumerate(rows):
            for x, line in row:
                # Mono and serif pieces share a baseline; each piece is its own <text> so it keeps its own size.
                for t, f, c in line:
                    size = ss if f.startswith('nr') else ms
                    s.text(x, y + r * lh * 0.82, [[(t, f, c)]], size)
                    x += width(t, f, size)
        s.add('</g>')
        y += lh * (1 + 0.82 * (len(rows) - 1))
    s.css.append('@media (prefers-reduced-motion: reduce){' + ','.join(f'.r{i}' for i in range(n)) + '{animation:none}}')
    s.h = y - lh + (32 if phone else 40)
    return s


def d2_principles(p, v):
    alt = 'Principles. ' + ' '.join(PRINCIPLES)
    s, phone, x, cw, y = d2_side_section(p, v, 'Principles', alt)
    size, lh, below, above = (19, 26, 17, 33) if phone else (23, 30, 19, 39)
    for i, line in enumerate(PRINCIPLES):
        end = s.text(x, y, wrap([(line, 'nr500', p['ink'])], size, cw), size, lh=lh)
        if i < len(PRINCIPLES) - 1:
            s.add(f'<line x1="{x}" y1="{end + below + .5:.1f}" x2="{x + cw}" y2="{end + below + .5:.1f}" stroke="{p["rule"]}"/>')
            y = end + below + above
    s.h = end + (32 if phone else 40)
    return s


# Shared so the colophon and the Say hi link sit on one baseline, with the same row height.
COLOPHON_BASE = 34


def d2_colophon(p, v):
    """One quiet line: a short rule, then the typefaces and how it is made, each family set in its own face.

    Desk is drawn at its natural width (it never shrinks, so 14 px stays 14 px) and the Say hi link sits right
    after it in the same row. Phone wraps the line and the link drops below it.
    """
    phone = v == 'phone'
    size, lh = 14, 21
    faces = ['nr400i', 'nr400', 'nr400i', 'pm400', 'nr400i']
    pieces = [(t, f, p['ink2'] if f in ('nr400', 'pm400') else p['ink3']) for t, f in zip(COLOPHON, faces)]
    W = 308 if phone else math.ceil(sum(width(t, f, size) for t, f, _ in pieces))
    s = Svg(W, 0, ''.join(COLOPHON))
    s.add(f'<line x1="0" y1=".5" x2="28" y2=".5" stroke="{p["ink3"]}"/>')
    end = s.text(0, COLOPHON_BASE, wrap(pieces, size, W), size, lh=lh)
    s.h = end + (14 if phone else 12)
    return s


def d2_say_hi(p, v):
    """The mail link: the colophon's row height on desk, so the two baselines line up."""
    size, base = 16, COLOPHON_BASE
    x = width(SAY_HI, 'nr400i', size) + 8
    s = Svg(math.ceil(x + 15), base + 12, f'{SAY_HI} \u2192')
    s.text(0, base, [[(SAY_HI, 'nr400i', p['acc'])]], size)
    mid = base - size * 0.3
    s.add(f'<path d="M{x:.1f} {mid:.1f}H{x + 15:.1f}M{x + 10:.1f} {mid - 4.5:.1f}L{x + 15:.1f} {mid:.1f}L{x + 10:.1f} {mid + 4.5:.1f}" '
          f'fill="none" stroke="{p["acc"]}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')
    s.add(f'<line x1="0" y1="{base + 8}" x2="{x + 15:.1f}" y2="{base + 8}" stroke="{p["acc"]}" stroke-width="1.5"/>')
    return s


def d2_avatar():
    s = Svg(460, 460, 'Epistex monogram')
    s.add('<rect width="460" height="460" fill="#ffffff"/>')
    w = width('E', 'nr500', 320)
    s.text(230 - w / 2, 330, [[('E', 'nr500', '#141414')]], 320)
    s.add('<path d="M140 362Q232 352 330 357" fill="none" stroke="#1d4ed8" stroke-width="12" stroke-linecap="round"/>')
    return s


def build():
    base = 'assets/editorial'
    themed(f'{base}/masthead', d2_masthead, D2, ['desk', 'phone'])
    themed(f'{base}/about', d2_about, D2, ['desk', 'phone'])
    themed(f'{base}/focus', d2_focus, D2, ['desk', 'phone'])
    themed(f'{base}/setup', d2_setup, D2, ['desk', 'phone'])
    themed(f'{base}/principles', d2_principles, D2, ['desk', 'phone'])
    themed(f'{base}/run', d2_run, D2, ['desk', 'phone'])
    themed(f'{base}/colophon', d2_colophon, D2, ['desk', 'phone'])
    themed(f'{base}/say-hi', d2_say_hi, D2, ['all'])
    save(f'{base}/avatar.svg', d2_avatar())
    agents_section = agents.build()
    readme = '\n'.join([
        f'<p>{pic(f"{base}/masthead", TAGLINE_ALT)}</p>',
        f'<p>{pic(f"{base}/about", f"About. {ABOUT}")}</p>',
        f'<p>{pic(f"{base}/focus", "Focus. " + " ".join(f"{i + 1}. {a}{b}" for i, (a, b) in enumerate(FOCUS)))}</p>',
        agents_section.rstrip('\n'),
        f'<p>{pic(f"{base}/setup", SETUP_ALT)}</p>',
        f'<p>{pic(f"{base}/principles", "Principles. " + " ".join(PRINCIPLES))}</p>',
        f'<p>{pic(f"{base}/run", RUN_ALT)}</p>',
        f'<p>{pic(f"{base}/colophon", "".join(COLOPHON))}{pic(f"{base}/say-hi", f"{SAY_HI} \u2192", "all", EMAIL_HREF)}</p>',
    ])
    with open(os.path.join(OUT, 'README.md'), 'w') as fh:
        fh.write(readme + '\n')


if __name__ == '__main__':
    build()
    size = sum(os.path.getsize(os.path.join(OUT, f)) for f in WRITTEN)
    print(f'{len(WRITTEN)} files, {size / 1024:.0f} KiB')
