"""The "How I run agents" section: an animated diagram and six steps that open in place (called by build.py).

Writes assets/agents/*.svg and returns the README section.

GitHub keeps no style or class and links inside an SVG do not click, so each diagram step is its own <img>, and
each step below the diagram is a <details> whose <summary> and body are images too. Every image runs its own CSS animation from load; all of them share one cycle length with the timing baked
into the keyframe percentages, so images loaded together stay in step. The static state (no animation, or
prefers-reduced-motion) is the complete diagram: the animation only ever hides or tints.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import D2, Svg, esc, label_steps, pic, save, width, wrap

P = {
    'light': dict(D2['light'], red='#cf222e', grn='#1a7f37', tint='#eef3ff'),
    'dark': dict(D2['dark'], red='#ff7b72', grn='#3fb950', tint='#1a2338'),
}
EASE = 'animation-timing-function:cubic-bezier(.23,1,.32,1)'
STEPS = [  # slug, title, note on the diagram and in the summary, sentences in the body
    ('you', 'You', '', ['I type one line: "add passkey login, keep passwords as fallback".',
                        'It touches the database, the server, the login screen and the browser test, so it becomes a task with a check for done.']),
    ('orchestrator', 'Orchestrator', 'no shell', ['The orchestrator has no shell and never edits code.',
                                                 'It writes four briefs, each with a scope and a check, and orders them: the schema lands first, the other three build on it.']),
    ('workers', 'Workers', 'in parallel', ['Four workers, one brief each: schema first, then three in parallel.',
                                          'Each writes a failing test first, sees it fail for its own reason, then makes it pass.']),
    ('self-review', 'Self-review', '', ['Each worker reviews its own diff before anyone else sees it.',
                                        'It reads every changed line against its brief and fixes what it finds.']),
    ('cross-model-review', 'Cross-model review', 'one round', ['A model from another family reviews once and finds what all four self-reviews missed: a used challenge is never deleted, so a replayed sign-in works.',
                                                               'It blocks because it has a reachable trigger, and it is fixed with a test.']),
    ('done', 'Done', 'with evidence', ['The result comes back with evidence: 128 tests passing in Chromium and WebKit, screenshots at 390 and 1440, and the pull request.',
                                       'Nothing is called done on confidence alone.']),
]
N = len(STEPS)
OUT_ASSETS = 'assets/agents'
SUM_PCT = 94                  # a summary image leaves room for the browser's disclosure marker


class Anim:
    """Keyframe classes on one cycle of T seconds; frames are (seconds or tuple of seconds, css)."""
    def __init__(self, s, T):
        self.s, self.T, self.n = s, T, 0
        s.css.append('@media (prefers-reduced-motion: reduce){*{animation:none!important}}')

    def pc(self, t):
        return f'{max(0.0, min(t, self.T)) / self.T * 100:.2f}%'

    def __call__(self, frames, base=''):
        self.n += 1
        c = f'a{self.n}'
        body = ''.join(f'{",".join(self.pc(t) for t in (ts if isinstance(ts, tuple) else (ts,)))}{{{css}}}' for ts, css in frames)
        # The reduced-motion rule must come last to win, so animated classes go before it.
        self.s.css.insert(len(self.s.css) - 1, f'.{c}{{{base}animation:k{c} {self.T:g}s linear infinite}}@keyframes k{c}{{{body}}}')
        return c

    def show(self, t, hold=None, dx=0, dy=6, dur=.4, extra=''):
        """Hidden until t, eases in, holds to `hold`, fades out before the loop."""
        hold = self.T - .8 if hold is None else hold
        return self([((0, t), f'opacity:0;transform:translate({dx}px,{dy}px){extra};{EASE}'),
                     ((t + dur, hold), 'opacity:1;transform:none'), ((hold + .4, self.T), 'opacity:0;transform:none')])


def T(s, x, y, t, f, c, size, anchor='start', cls='', ls=0):
    return s.text(x, y, [[(t, f, c)]], size, anchor=anchor, cls=cls, ls=ls)


# ------------------------------------------------------------------ geometry
def seg_pt(seg, u):
    if seg[0] == 'L':
        (x0, y0), (x1, y1) = seg[1], seg[2]
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = seg[1:]
    a, b, c, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
    return a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3


def path_d(segs):
    d = f'M{segs[0][1][0]:.1f} {segs[0][1][1]:.1f}'
    for sg in segs:
        d += f'L{sg[2][0]:.1f} {sg[2][1]:.1f}' if sg[0] == 'L' else 'C' + ' '.join(f'{x:.1f} {y:.1f}' for x, y in sg[2:])
    return d


def samples(segs, n):
    pts = [seg_pt(sg, k / 24) for sg in segs for k in range(25)]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    out, j = [], 0
    for k in range(n + 1):
        target = cum[-1] * k / n
        while j < len(cum) - 2 and cum[j + 1] < target:
            j += 1
        out.append(pts[j + 1] if cum[j + 1] <= target else pts[j])
    return out, cum[-1]


def chevron(x, y, d, c):
    pts = f'M{x - 6} {y - 4}L{x} {y}L{x - 6} {y + 4}' if d == 'r' else f'M{x - 4} {y - 6}L{x} {y}L{x + 4} {y - 6}'
    return f'<path d="{pts}" fill="none" stroke="{c}" stroke-width="1.25" stroke-linejoin="round"/>'


def check(x, y, k, c, w=2):
    return (f'<path d="M{x:.1f} {y:.1f}L{x + 5 * k:.1f} {y + 5 * k:.1f}L{x + 14 * k:.1f} {y - 6 * k:.1f}" fill="none" stroke="{c}" '
            f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def cross(x, y, k, c, w=2):
    return (f'<path d="M{x:.1f} {y - 5 * k:.1f}L{x + 10 * k:.1f} {y + 5 * k:.1f}M{x + 10 * k:.1f} {y - 5 * k:.1f}L{x:.1f} {y + 5 * k:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>')


def arrow(x0, y0, x1, y1, c, w=1.4):
    ang = math.atan2(y1 - y0, x1 - x0)
    a1, a2 = ang + 2.6, ang - 2.6
    return (f'<path d="M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}M{x1 + 8 * math.cos(a1):.1f} {y1 + 8 * math.sin(a1):.1f}L{x1:.1f} {y1:.1f}'
            f'L{x1 + 8 * math.cos(a2):.1f} {y1 + 8 * math.sin(a2):.1f}" fill="none" stroke="{c}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# ------------------------------------------------------------------ the diagram
DT = 7.0                      # cycle, seconds
T0, DSTEP = .4, 1.0           # node i lights at T0 + i * DSTEP
LIT_END = 6.3                 # every node stays lit to here, then all fade back before the loop
NODE_PCT, CONN_PCT = 13.7, 3.25
NW, CW = 116, 27.5            # viewBox widths, so NODE_PCT of an 846 column is ~1:1
Y, SPREAD = 34, 21
FAN = (-21, -7, 7, 21)        # the four worker lanes; 14 apart stays ~9 px at a 563 column
TITLE, NOTE = 19, 18.5        # >= 12 px when the row shrinks to a 563 column


def t_node(i):
    return T0 + i * DSTEP


def light(s, a, segs, t0, t1, p, n=12):
    """A blue light along segs from t0 to t1, with the path tracing blue behind it until LIT_END."""
    pts, _ = samples(segs, n)
    d = path_d(segs)
    tr = a([((0, t0), 'stroke-dashoffset:1;opacity:1'), ((t1, LIT_END), 'stroke-dashoffset:0;opacity:1'),
            (LIT_END + .4, 'stroke-dashoffset:0;opacity:0'), (a.T, 'stroke-dashoffset:1;opacity:0')],
           base='stroke-dasharray:1 2;stroke-dashoffset:1;')
    s.add(f'<path class="{tr}" d="{d}" pathLength="1" fill="none" stroke="{p["acc"]}" stroke-width="1.6"/>')
    fr = [((0, t0), f'opacity:0;transform:translate({pts[0][0]:.1f}px,{pts[0][1]:.1f}px)')]
    for k, (x, y) in enumerate(pts):
        fr.append((t0 + (t1 - t0) * k / n, f'opacity:1;transform:translate({x:.1f}px,{y:.1f}px)'))
    fr.append(((t1 + .1, a.T), f'opacity:0;transform:translate({pts[-1][0]:.1f}px,{pts[-1][1]:.1f}px)'))
    c = a(fr, base='opacity:0;')
    s.add(f'<g class="{c}"><circle r="8" fill="{p["acc"]}" opacity=".18"/><circle r="3.6" fill="{p["acc"]}"/></g>')


def node_dot(s, a, cx, cy, ti, p, last):
    lit = a([((0, ti), f'fill:{p["acc"] if last else p["bg"]};stroke:{p["acc"] if last else p["ink"]}'),
             ((ti + .12, LIT_END), f'fill:{p["acc"]};stroke:{p["acc"]}'),
             ((LIT_END + .4, a.T), f'fill:{p["acc"] if last else p["bg"]};stroke:{p["acc"] if last else p["ink"]}')])
    ring = a([((0, ti), 'opacity:0;transform:scale(.4)'), (ti + .02, 'opacity:.55;transform:scale(.4)'),
              ((ti + .7, a.T), 'opacity:0;transform:scale(1)')], base='opacity:0;transform-box:fill-box;transform-origin:center;')
    s.add(f'<circle class="{ring}" cx="{cx}" cy="{cy}" r="15" fill="none" stroke="{p["acc"]}" stroke-width="1.5"/>')
    if last:
        s.add(f'<circle class="{lit}" cx="{cx}" cy="{cy}" r="5.5" fill="{p["acc"]}" stroke="{p["acc"]}" stroke-width="1.5"/>')
    else:
        s.add(f'<circle class="{lit}" cx="{cx}" cy="{cy}" r="4.5" fill="{p["bg"]}" stroke="{p["ink"]}" stroke-width="1.5"/>')


def title_lit(a, ti, p):
    return a([((0, ti), f'fill:{p["ink"]}'), ((ti + .15, LIT_END), f'fill:{p["acc"]}'), ((LIT_END + .4, a.T), f'fill:{p["ink"]}')])


def node_text_height():
    bottom = 0
    for slug, title, note, _ in STEPS:
        lines = wrap([(title, 'nr600', '#000')], TITLE, NW - 6)
        end = Y + SPREAD + 40 + (len(lines) - 1) * 23
        if note:
            end += 25 + (len(wrap([(note, 'nr400i', '#000')], NOTE, NW - 6)) - 1) * 23
        bottom = max(bottom, end)
    return bottom + 22


def desk_stub_segs(i):
    """The line leaving node i inside its own image: straight, splitting (Orchestrator) or merging (Workers)."""
    if i == 1:
        return [[('L', (15, Y), (NW - 56, Y)), ('C', (NW - 56, Y), (NW - 26, Y), (NW - 26, Y + dy), (NW, Y + dy))] for dy in FAN]
    if i == 2:
        return [[('L', (15, Y + dy), (44, Y + dy)), ('C', (44, Y + dy), (74, Y + dy), (74, Y), (NW, Y))] for dy in FAN]
    return [[('L', (15, Y), (NW, Y))]]


def desk_times(i):
    """(stub start, stub end, connector end) of the light leaving node i; constant speed across both images."""
    a0, a2 = t_node(i) + .12, t_node(i + 1) - .06
    stub = NW - 15
    return a0, a0 + (a2 - a0) * stub / (stub + CW), a2


def d_node(p, i, H):
    slug, title, note, _ = STEPS[i]
    s = Svg(NW, H, title)
    a = Anim(s, DT)
    line = f'fill="none" stroke="{p["ink3"]}" stroke-width="1.25"'
    ti = t_node(i)
    if i < N - 1:
        a0, a1, _ = desk_times(i)
        for segs in desk_stub_segs(i):
            s.add(f'<path d="{path_d(segs)}" {line}/>')
        for segs in desk_stub_segs(i):
            light(s, a, segs, a0, a1, p)
    for k, dy in enumerate(FAN if i == 2 else (0,)):
        node_dot(s, a, 8, Y + dy, ti + .1 * k, p, i == N - 1)
    tl = title_lit(a, ti, p)
    lines = wrap([(title, 'nr600', p['ink'])], TITLE, NW - 6)
    y = Y + SPREAD + 40
    end = s.text(2, y, lines, TITLE, lh=23, cls=tl)
    s.css.append(f'.{tl} tspan{{animation:inherit}}')
    if note:
        s.text(2, end + 29, wrap([(note, 'nr400i', p['ink2'])], NOTE, NW - 6), NOTE, lh=23)
    return s


def d_conn(p, i, H):
    s = Svg(CW, H, '')
    a = Anim(s, DT)
    line = f'fill="none" stroke="{p["ink3"]}" stroke-width="1.25"'
    _, a1, a2 = desk_times(i)
    for dy in (FAN if i == 1 else (0,)):
        segs = [('L', (0, Y + dy), (CW - 2, Y + dy))]
        s.add(f'<path d="{path_d(segs)}" {line}/>' + chevron(CW - 2, Y + dy, 'r', p['ink3']))
        light(s, a, segs, a1, a2, p, n=3)
    return s


# Phone: one 308 px image per step, stacked; each carries its own outgoing line down to an arrowhead.
PX, PY = 21, 16
PFAN = (-15, -5, 5, 15)


def phone_h(i):
    note = STEPS[i][2]
    return (PY + 6 + 22 + (24 if note else 0) + 6) if i < N - 1 else PY + 6 + 26 + (24 if note else 0)


def phone_segs(i, H):
    b = H - 3
    if i == 1:
        return [[('L', (PX, PY + 7), (PX, b - 26)), ('C', (PX, b - 26), (PX, b - 12), (PX + dx, b - 14), (PX + dx, b))] for dx in PFAN]
    if i == 2:
        return [[('L', (PX + dx, PY + 7), (PX + dx, PY + 12)), ('C', (PX + dx, PY + 12), (PX + dx, b - 14), (PX, b - 18), (PX, b))] for dx in PFAN]
    return [[('L', (PX, PY + 7), (PX, b))]]


def p_node(p, i):
    slug, title, note, _ = STEPS[i]
    H = phone_h(i)
    s = Svg(308, H, title)
    a = Anim(s, DT)
    line = f'fill="none" stroke="{p["ink3"]}" stroke-width="1.25"'
    ti = t_node(i)
    if i < N - 1:
        segs_all = phone_segs(i, H)
        for segs in segs_all:
            s.add(f'<path d="{path_d(segs)}" {line}/>')
        heads = [(segs[-1][-1]) for segs in segs_all] if i != 2 else [segs_all[0][-1][-1]]
        for x, y in heads:
            s.add(chevron(x, y, 'd', p['ink3']))
        for segs in segs_all:
            light(s, a, segs, ti + .12, t_node(i + 1) - .06, p)
    for k, dx in enumerate(PFAN if i == 2 else (0,)):
        node_dot(s, a, PX + dx, PY, ti + .1 * k, p, i == N - 1)
    tl = title_lit(a, ti, p)
    T(s, 44, PY + 6, title, 'nr600', p['ink'], 18, cls=tl)
    s.css.append(f'.{tl} tspan{{animation:inherit}}')
    if note:
        T(s, 44, PY + 30, note, 'nr400i', p['ink2'], 16)
    return s


def label(p, v):
    W = 308 if v == 'phone' else 846
    s = Svg(W, 62, 'How I run agents')
    s.add(f'<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{p["rule"]}"/>')
    T(s, 0, 42, 'How I run agents', 'nr400i', p['acc'], 20 if W > 400 else 18)
    if v == 'phone':
        T(s, W - 16, 42, 'open a step', 'nr400i', p['ink3'], 14, anchor='end')
        s.add(arrow(W - 6, 30, W - 6, 44, p['ink3'], 1.2))
    else:
        s.css.append(label_steps(14, W))
        T(s, W - 20, 42, 'open a step', 'nr400i', p['ink3'], 14, anchor='end', cls='lab')
        s.add(arrow(W - 8, 30, W - 8, 44, p['ink3'], 1.2))
    return s


EMPTY = '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1"/>'
# Stands in for a desktop row image on phones: its percent width stays, its height becomes ~0.
EMPTY_ROW = '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1" viewBox="0 0 1000 1"/>'

ALT = {
    'you': 'You: a request in plain words.', 'orchestrator': 'Orchestrator: no shell, writes briefs and delegates.',
    'workers': 'Workers, in parallel: a failing test first, then the fix.', 'self-review': 'Self-review of the diff.',
    'cross-model-review': 'Cross-model review, one round.', 'done': 'Done, with evidence.',
}


def build_diagram():
    H = node_text_height()
    for theme, p in P.items():
        save(f'{OUT_ASSETS}/label-{"desk"}-{theme}.svg', label(p, 'desk'))
        save(f'{OUT_ASSETS}/label-{"phone"}-{theme}.svg', label(p, 'phone'))
        for i, st in enumerate(STEPS):
            save(f'{OUT_ASSETS}/node-{st[0]}-desk-{theme}.svg', d_node(p, i, H))
            save(f'{OUT_ASSETS}/node-{st[0]}-phone-{theme}.svg', p_node(p, i))
            if i < N - 1:
                save(f'{OUT_ASSETS}/conn-{i + 1}-desk-{theme}.svg', d_conn(p, i, H))
    save(f'{OUT_ASSETS}/empty.svg', EMPTY)
    save(f'{OUT_ASSETS}/empty-row.svg', EMPTY_ROW)


def pic_label(base):
    return (f'<picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="{base}/label-phone-dark.svg">'
            f'<source media="(max-width: 600px)" srcset="{base}/label-phone-light.svg">'
            f'<source media="(prefers-color-scheme: dark)" srcset="{base}/label-desk-dark.svg">'
            f'<img src="{base}/label-desk-light.svg" alt="How I run agents (open a step below)"></picture>')


def pic_row(src, alt, pct, base):
    return (f'<picture><source media="(max-width: 600px)" srcset="{base}/empty-row.svg">'
            f'<source media="(prefers-color-scheme: dark)" srcset="{base}/{src}-desk-dark.svg">'
            f'<img src="{base}/{src}-desk-light.svg" width="{pct}%" alt="{esc(alt)}"></picture>')


def pic_phone(src, alt, base):
    return (f'<picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="{base}/{src}-phone-dark.svg">'
            f'<source media="(max-width: 600px)" srcset="{base}/{src}-phone-light.svg">'
            f'<img src="{base}/empty.svg" alt="{esc(alt)}"></picture>')


def details_md(i, base):
    """One closed <details>: a summary image, then the sentences and the animated visual in one <p>."""
    slug, title, note, sentences = STEPS[i]
    label = f'{i + 1} {title}' + (f' · {note}' if note else '')
    return (f'<details><summary>{pic(f"{base}/{slug}-sum", label, width=SUM_PCT, align="middle")}</summary>'
            f'<p>{pic(f"{base}/{slug}-text", " ".join(sentences))}'
            f'{pic(f"{base}/{slug}-visual", SCENES[slug](P["light"], "desk").title)}</p></details>')


def section_md(base='assets/agents'):
    """The diagram as one <p>, no whitespace between images: the label, the phone stack (1 px dots on desktop), then the
    desktop row (zero-height on phones, so its line sits at the bottom of the section as spacing). Then the six steps."""
    phone = ''.join(pic_phone('node-' + st[0], ALT[st[0]], base) for st in STEPS)
    row = ''
    for i, st in enumerate(STEPS):
        row += pic_row('node-' + st[0], ALT[st[0]], NODE_PCT, base)
        if i < N - 1:
            row += pic_row(f'conn-{i + 1}', '', CONN_PCT, base)
    return '\n'.join([f'<p>{pic_label(base)}{phone}{row}</p>'] + [details_md(i, base) for i in range(N)]) + '\n'


# ------------------------------------------------------------------ the steps
ST = 8.0  # every step visual loops in 8 s


def summary(p, v, i):
    """The <summary> of step i: its number, name and note, with a thin rule above (the steps read as a ruled index)."""
    slug, title, note, _ = STEPS[i]
    ph = v == 'phone'
    W = 308 if ph else 846
    n, ts, ns = (18, 20, 16) if ph else (22, 26, 21)
    tx = 28 if ph else 38
    one_line = not ph or not note or tx + width(title, 'nr600', ts) + 12 + width(f'· {note}', 'nr400i', ns) <= W
    s = Svg(W, 56 if one_line else 80, f'{i + 1} {title}' + (f' · {note}' if note else ''))
    s.add(f'<line x1="0" y1=".5" x2="{W}" y2=".5" stroke="{p["rule"]}"/>')
    y = 41 if ph else 42
    T(s, 0, y, str(i + 1), 'nr400i', p['acc'], n)
    T(s, tx, y, title, 'nr600', p['ink'], ts)
    if note:
        if one_line:
            T(s, tx + width(title, 'nr600', ts) + 12, y, f'· {note}', 'nr400i', p['ink2'], ns)
        else:
            T(s, tx, y + 26, note, 'nr400i', p['ink2'], ns)
    return s


def caption(p, v, i):
    """The step's sentences, set in the body of its <details> above the visual."""
    sentences = STEPS[i][3]
    W = 308 if v == 'phone' else 846
    size, lh, bw = (18, 27, W) if v == 'phone' else (21, 32, 780)
    s = Svg(W, 0, ' '.join(sentences))
    y = 34
    for k, sent in enumerate(sentences):
        end = s.text(0, y, wrap([(sent, 'nr400', p['ink'] if k == 0 else p['ink2'])], size, bw), size, lh=lh)
        y = end + lh + 4
    s.h = end + 24
    return s


def box(s, x, y, w, h, stroke, fill=None, sw=1, rx=3, cls=''):
    c = f' class="{cls}"' if cls else ''
    s.add(f'<rect{c} x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill or "none"}" stroke="{stroke}" stroke-width="{sw}"/>')


INTENT = 'add passkey login, keep passwords as fallback'
INTENT_PHONE = ['add passkey login,', 'keep passwords as fallback']
PARTS = ['schema', 'server', 'ui', 'e2e']


def chip(s, x, y, txt, font, size, stroke, col, h, padx=12, sw=1.2):
    w = width(txt, font, size) + 2 * padx
    box(s, x, y, w, h, stroke, sw=sw)
    T(s, x + padx, y + h / 2 + size * .35, txt, font, col, size)
    return w


def typed_lines(s, a, x, y0, lines, ms, lh, t0, t1, p, cid):
    """Types the lines one after another between t0 and t1, with a caret riding the last typed character."""
    cw = width('a', 'pm400', ms)
    total = sum(len(l) for l in lines)
    t, caret = t0, [((0, t0), f'transform:translate(0px,0px);opacity:1')]
    for k, line in enumerate(lines):
        n = len(line)
        te = t + (t1 - t0) * n / total
        clip = a([((0, t), 'transform:scaleX(0)'), ((te, ST - .4), 'transform:scaleX(1)'), (ST, 'transform:scaleX(1)')],
                 base='transform-box:fill-box;transform-origin:left;animation-timing-function:steps(%d,end)!important;' % n)
        yy = y0 + k * lh
        s.add(f'<defs><clipPath id="{cid}{k}"><rect class="{clip}" x="{x}" y="{yy - ms - 4}" width="{n * cw:.1f}" height="{ms + 12}"/></clipPath></defs>')
        s.add(f'<g clip-path="url(#{cid}{k})">')
        T(s, x, yy, line, 'pm400', p['ink'], ms)
        s.add('</g>')
        caret.append((t + .001, f'transform:translate(0px,{k * lh}px);opacity:1'))
        caret.append((te, f'transform:translate({n * cw:.1f}px,{k * lh}px);opacity:1'))
        t = te
    xe, ye = len(lines[-1]) * cw, (len(lines) - 1) * lh
    caret += [((t1 + .2, t1 + .6), f'transform:translate({xe:.1f}px,{ye}px);opacity:0'), (t1 + .4, f'transform:translate({xe:.1f}px,{ye}px);opacity:1'),
              ((t1 + .65, ST), f'transform:translate({xe:.1f}px,{ye}px);opacity:0')]
    c = a(caret, base='opacity:0;')
    s.add(f'<rect class="{c}" x="{x}" y="{y0 - ms + 1}" width="2" height="{ms + 2}" fill="{p["acc"]}"/>')


def scene_you(p, v):
    ph = v == 'phone'
    W = 308 if ph else 846
    s = Svg(W, 0, f'One line is typed, "{INTENT}", and becomes a task card that touches four parts '
                  '(schema, server, ui, e2e) with a done-means check.')
    a = Anim(s, ST)
    ms = 15 if ph else 20
    lab = 15 if ph else 18.5
    T(s, 0, 24, 'the intent, typed once', 'nr400i', p['ink3'], lab)
    lines = INTENT_PHONE if ph else [INTENT]
    lh = 26
    bh = 54 + (len(lines) - 1) * lh
    box(s, 0, 40, W, bh, p['ink3'])
    T(s, 16, 74, '>', 'pm400', p['ink3'], ms)
    typed_lines(s, a, 16 + ms * 1.2, 74, lines, ms, lh, .3, 2.5, p, 'typ')
    if not ph:
        T(s, W - 16, 74, '1 line', 'nr400i', p['ink3'], lab, anchor='end', cls=a.show(2.7, dy=0))
    ay = 40 + bh + 10
    s.add(f'<g class="{a.show(3.0, dy=-8)}">{arrow(28, ay, 28, ay + 30, p["ink3"])}</g>')
    cx, cy, cw = 0, ay + 44, W
    ins = 18 if ph else 22
    card = a.show(3.2, dy=-16)
    s.add(f'<g class="{card}">')
    T(s, cx + ins, cy + 34, 'TASK', 'pm500', p['ink3'], 13 if ph else 18.5, ls=2)
    tsz = 22 if ph else 26
    T(s, cx + ins, cy + (66 if ph else 76), 'Add passkey login', 'nr600', p['ink'], tsz)
    y = cy + (86 if ph else 100)
    s.add(f'<line x1="{cx + ins}" y1="{y}" x2="{cx + cw - ins}" y2="{y}" stroke="{p["rule"]}"/>')
    s.add('</g>')
    fs = 15 if ph else 19
    # goal, then the four parts it touches: side by side on desktop, stacked on phones.
    g1 = a.show(3.7)
    gx, gy = cx + ins, y + (30 if ph else 36)
    gw = (cw - 2 * ins) if ph else 360
    s.add(f'<g class="{g1}">')
    T(s, gx, gy, 'goal', 'nr400i', p['ink3'], lab)
    gend = s.text(gx, gy + (24 if ph else 30), wrap([('Sign in with a passkey; passwords still work.', 'nr400', p['ink'])], fs, gw), fs, lh=fs * 1.35)
    s.add('</g>')
    tx, ty = (gx, gend + 34) if ph else (cx + 420, gy)
    T(s, tx, ty, 'touches', 'nr400i', p['ink3'], lab, cls=a.show(4.0))
    chx, chy = tx, ty + (12 if ph else 14)
    chh = 30 if ph else 38
    for k, part in enumerate(PARTS):
        g = a.show(4.1 + .2 * k, dy=0, extra=' scale(.9)')
        s.add(f'<g class="{g}" style="transform-box:fill-box;transform-origin:center">')
        chx += chip(s, chx, chy, part, 'pm500', 14 if ph else 18.5, p['acc'], p['acc'], chh, padx=10 if ph else 14) + (8 if ph else 12)
        s.add('</g>')
    T(s, tx, chy + chh + (24 if ph else 32), 'four parts that must fit together', 'nr400i', p['ink2'], 14 if ph else 18.5, cls=a.show(5.0))
    y = max(gend, chy + chh + (24 if ph else 32)) + (26 if ph else 30)
    s.add(f'<g class="{a.show(5.2)}">')
    s.add(f'<line x1="{cx + ins}" y1="{y}" x2="{cx + cw - ins}" y2="{y}" stroke="{p["rule"]}"/>')
    y += 34 if ph else 40
    T(s, cx + ins, y, 'done means\u2026', 'nr400i', p['ink3'], lab)
    y += 30
    box(s, cx + ins, y - 16, 18, 18, p['acc'], sw=1.5, rx=2)
    dsz = 13.5 if ph else 18.5
    end = s.text(cx + ins + 30, y - 2, wrap([('e2e passes in Chromium and WebKit', 'pm400', p['ink'])], dsz, cw - 2 * ins - 30), dsz, lh=22)
    s.add('</g>')
    tick = a.show(5.9, dy=0, extra=' scale(.6)')
    s.add(f'<g class="{tick}" style="transform-box:fill-box;transform-origin:center">{check(cx + ins + 3.5, y - 7.5, .8, p["acc"], 2.2)}</g>')
    ch = end + 28 - cy
    s.add(f'<g class="{card}">')
    box(s, cx, cy, cw, ch, p['ink3'])
    s.add('</g>')
    s.h = cy + ch + 4
    return s


def terminal_lock(s, x, y, p, k=1.0):
    w, h = 64 * k, 46 * k
    box(s, x, y, w, h, p['ink3'], rx=3)
    s.add(f'<line x1="{x:.1f}" y1="{y + 11 * k:.1f}" x2="{x + w:.1f}" y2="{y + 11 * k:.1f}" stroke="{p["ink3"]}"/>')
    for d in (6, 12, 18):
        s.add(f'<circle cx="{x + d * k:.1f}" cy="{y + 5.5 * k:.1f}" r="{1.6 * k:.1f}" fill="{p["ink3"]}"/>')
    T(s, x + 8 * k, y + 34 * k, '$_', 'pm500', p['ink3'], 15 * k)
    lx, ly = x + w - 14 * k, y + h - 6 * k
    s.add(f'<rect x="{lx - 9 * k:.1f}" y="{ly - 13 * k:.1f}" width="{18 * k:.1f}" height="{14 * k:.1f}" rx="2" fill="{p["ink"]}"/>'
          f'<path d="M{lx - 5.5 * k:.1f} {ly - 13 * k:.1f}V{ly - 17 * k:.1f}A{5.5 * k:.1f} {5.5 * k:.1f} 0 0 1 {lx + 5.5 * k:.1f} {ly - 17 * k:.1f}V{ly - 13 * k:.1f}" fill="none" stroke="{p["ink"]}" stroke-width="{2 * k:.1f}"/>'
          f'<circle cx="{lx:.1f}" cy="{ly - 6 * k:.1f}" r="{1.8 * k:.1f}" fill="{p["bg"]}"/>')


BRIEFS = [('schema', 'credentials table and its migration', 'migrate up and down'),
          ('server', 'WebAuthn register and sign-in endpoints, challenge store', 'a valid assertion verifies'),
          ('ui', '\u201cSign in with a passkey\u201d button, password fallback', 'renders at 390 and 1440'),
          ('e2e', 'virtual authenticator: register, then sign in', 'passes in Chromium and WebKit')]


def brief(s, x, y, w, k, p, ph, tag=None):
    """A brief card (name, scope, check); returns its height."""
    ns, fs, cs = (14, 15, 13) if ph else (18.5, 18.5, 18.5)
    name, scope, chk = BRIEFS[k]
    pad = 12 if ph else 16
    yy = y + (22 if ph else 30)
    T(s, x + pad, yy, name, 'pm500', p['acc'], ns)
    if tag:
        T(s, x + w - pad, yy, tag, 'nr400i', p['acc'], 14 if ph else 18.5, anchor='end')
    end = s.text(x + pad, yy + (22 if ph else 30), wrap([(scope, 'nr400', p['ink'])], fs, w - 2 * pad), fs, lh=fs * 1.3)
    cy = end + (22 if ph else 30)
    T(s, x + pad, cy, 'check', 'pm400', p['ink3'], cs)
    cx = x + pad + width('check ', 'pm400', cs) + 4
    s.text(cx, cy, wrap([(chk, 'nr400i', p['ink2'])], 14 if ph else 18.5, x + w - pad - cx), 14 if ph else 18.5, lh=20)
    h = cy - y + (14 if ph else 18)
    box(s, x, y, w, h, p['acc'], sw=1.3)
    return h


def scene_orchestrator(p, v):
    ph = v == 'phone'
    W = 308 if ph else 846
    s = Svg(W, 0, 'The orchestrator has no shell. It turns the task into four briefs, each with a scope and a check: '
                  'schema lands first, then server, ui and e2e build on it in parallel.')
    a = Anim(s, ST)
    tw = W if ph else 280
    th = 100 if ph else 128
    box(s, 0, 0, tw, th, p['ink3'])
    T(s, 18, 28 if ph else 36, 'TASK', 'pm500', p['ink3'], 13 if ph else 18.5, ls=2)
    T(s, 18, 58 if ph else 74, 'Add passkey login', 'nr600', p['ink'], 20 if ph else 22)
    T(s, 18, 82 if ph else 104, 'passwords as fallback', 'nr400i', p['ink2'], 14 if ph else 18.5)
    ly = th + (18 if ph else 36)
    k_l = .9 if ph else 1.25
    terminal_lock(s, 0, ly, p, k_l)
    nx = 74 if ph else 100
    T(s, nx, ly + (20 if ph else 26), 'no shell', 'nr600', p['ink'], 17 if ph else 20)
    s.text(nx, ly + (42 if ph else 52), wrap([('never edits code, only delegates', 'nr400i', p['ink2'])], 14 if ph else 18.5, W - nx if ph else 180), 14 if ph else 18.5, lh=22)
    if ph:
        tx, ty, tw2, ind = 0, ly + 76, W, 22
    else:
        tx, ty, tw2, ind = 330, 0, W - 330, 40
    # schema flies out of the task card first; the spine then carries the other three briefs off it.
    fly = a([((0, .7), f'opacity:0;transform:translate({-tx + 10:.0f}px,{10 - ty:.0f}px) scale(.8)'),
             (.9, f'opacity:1;transform:translate({-tx + 10:.0f}px,{10 - ty:.0f}px) scale(.8);{EASE}'),
             ((1.7, ST - .8), 'opacity:1;transform:none'), ((ST - .4, ST), 'opacity:0;transform:none')])
    s.add(f'<g class="{fly}">')
    h0 = brief(s, tx, ty, tw2, 0, p, ph, tag='lands first')
    s.add('</g>')
    y = ty + h0 + (26 if ph else 34)
    note = a.show(2.0, dx=-6, dy=0)
    s.text(tx + ind, y, wrap([('then three in parallel, built on it', 'nr400i', p['ink2'])], 14 if ph else 18.5, tw2 - ind), 14 if ph else 18.5, cls=note)
    y += 14 if ph else 18
    sx = tx + ind / 2
    mids = []
    for k in (1, 2, 3):
        g = a.show(2.4 + .3 * (k - 1), dx=-12, dy=0)
        s.add(f'<g class="{g}">')
        h = brief(s, tx + ind, y, tw2 - ind, k, p, ph)
        s.add('</g>')
        mids.append(y + (18 if ph else 24))
        y += h + (12 if ph else 14)
    sp = a([((0, 1.9), 'stroke-dashoffset:1'), ((2.6, ST - .8), 'stroke-dashoffset:0;opacity:1'), ((ST - .4, ST), 'stroke-dashoffset:0;opacity:0')],
           base='stroke-dasharray:1 2;')
    d = f'M{sx:.1f} {ty + h0:.1f}V{mids[-1]:.1f}' + ''.join(f'M{sx:.1f} {m:.1f}H{tx + ind:.1f}' for m in mids)
    s.add(f'<path class="{sp}" d="{d}" pathLength="1" fill="none" stroke="{p["acc"]}" stroke-width="1.5"/>')
    s.h = y - (12 if ph else 14) + 4
    return s


LANES = [('schema', 'relation "credentials" does not exist', '+38 -0'),
         ('server', 'expected verified, got 404', '+112 -4'),
         ('ui', 'button not found', '+46 -9'),
         ('e2e', 'no passkey prompt', '+64 -0')]
LANE_SCOPE = ['credentials table', 'WebAuthn endpoints', 'passkey button', 'virtual authenticator']


def lane_times(k):
    """(fail, code, pass) of lane k: schema runs first, the other three together once it is green."""
    b = .4 if k == 0 else 2.3 + .2 * (k - 1)
    st = .9 if k == 0 else 1.0
    return b, b + st, b + 2 * st


def scene_workers(p, v):
    ph = v == 'phone'
    W = 308 if ph else 846
    s = Svg(W, 0, 'Four workers. Schema goes first; then server, ui and e2e run in parallel. Each lane goes from a failing '
                  'test, with its own reason, to the code change, to the test passing.')
    a = Anim(s, ST)
    lh = 116 if ph else 150
    for k, (name, reason, diff) in enumerate(LANES):
        tf, tc, tp = lane_times(k)
        y0 = k * lh
        T(s, 0, y0 + 18, name, 'pm500', p['ink'], 14 if ph else 18.5)
        T(s, 62 if ph else 96, y0 + 18, LANE_SCOPE[k], 'nr400i', p['ink3'], 14 if ph else 19)
        T(s, W, y0 + 18, 'first' if k == 0 else 'in parallel', 'nr400i', p['acc'] if k == 0 else p['ink3'], 14 if ph else 18.5, anchor='end')
        cy = y0 + (30 if ph else 38)
        chh = 40 if ph else 56
        xs, cwid = ([0, 108, 216], 92) if ph else ([0, 300, 600], 246)
        mid = cy + chh / 2
        s.add(f'<line x1="{xs[0] + cwid}" y1="{mid}" x2="{xs[1]}" y2="{mid}" stroke="{p["rule"]}"/>'
              f'<line x1="{xs[1] + cwid}" y1="{mid}" x2="{xs[2]}" y2="{mid}" stroke="{p["rule"]}"/>')
        for j, (t0, t1) in enumerate([(tf + .3, tc), (tc + .3, tp)]):
            lx0, lx1 = xs[j] + cwid, xs[j + 1]
            c = a([((0, t0), f'opacity:0;transform:translateX({lx0}px)'), (t0 + .02, f'opacity:1;transform:translateX({lx0}px)'),
                   (t1, f'opacity:1;transform:translateX({lx1}px)'), ((t1 + .08, ST), f'opacity:0;transform:translateX({lx1}px)')], base='opacity:0;')
            s.add(f'<g class="{c}"><circle cx="0" cy="{mid}" r="8" fill="{p["acc"]}" opacity=".18"/><circle cx="0" cy="{mid}" r="3.6" fill="{p["acc"]}"/></g>')
        fs = 15 if ph else 19
        g = a.show(tf, dy=0, extra=' scale(.94)')
        s.add(f'<g class="{g}" style="transform-box:fill-box;transform-origin:center">')
        box(s, xs[0], cy, cwid, chh, p['red'], sw=1.4)
        s.add(cross(xs[0] + 14, mid, .9 if ph else 1.1, p['red']))
        T(s, xs[0] + (32 if ph else 40), mid + fs * .34, 'fails' if ph else 'test fails', 'nr600', p['red'], fs)
        s.add('</g>')
        rs = 12.5 if ph else 18.5
        g = a.show(tf + .35, dy=4)
        s.text(xs[0], cy + chh + (20 if ph else 30), [[(reason, 'pm400', p['ink2'])]], rs, cls=g)
        g = a.show(tc, dy=0, extra=' scale(.94)')
        s.add(f'<g class="{g}" style="transform-box:fill-box;transform-origin:center">')
        box(s, xs[1], cy, cwid, chh, p['ink3'], sw=1.2)
        if ph:
            T(s, xs[1] + cwid / 2, mid + 5, diff, 'pm500', p['ink'], 13.5, anchor='middle')
        else:
            T(s, xs[1] + 20, mid + 6.5, 'code', 'nr600', p['ink'], fs)
            T(s, xs[1] + cwid - 20, mid + 6.5, diff, 'pm500', p['ink2'], 18.5, anchor='end')
        s.add('</g>')
        g = a.show(tp, dy=0, extra=' scale(.94)')
        s.add(f'<g class="{g}" style="transform-box:fill-box;transform-origin:center">')
        box(s, xs[2], cy, cwid, chh, p['grn'], sw=1.4)
        s.add(check(xs[2] + 12, mid, .9 if ph else 1.1, p['grn'], 2.2))
        T(s, xs[2] + (32 if ph else 40), mid + fs * .34, 'passes' if ph else 'test passes', 'nr600', p['grn'], fs)
        s.add('</g>')
    s.h = 3 * lh + (30 + 40 + 20 + 8 if ph else 38 + 56 + 30 + 10)
    return s


DIFF = [('+', "router.post('/passkey/verify')"), ('+', 'const ch = challenges.get(user)'),
        ('+', 'const ok = verify(assertion, ch)'), ('+', 'if (!ok) return res.status(401)'), ('+', 'return signIn(res, user)')]
DIFF_HEAD = 'server \u00b7 webauthn.ts \u00b7 +112 -4'


def diff_panel(s, a, x, y, w, p, ph, lines, scan, tick_col=None, head=DIFF_HEAD):
    ms = 12.5 if ph else 18.5
    lh = 28 if ph else 38
    hh = 30 if ph else 42
    s.add(f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" fill="{p["tint"]}"/>')
    T(s, x + 12, y + hh / 2 + ms * .35, head, 'pm400', p['ink3'], ms)
    for k, (sign, code) in enumerate(lines):
        yy = y + hh + 10 + k * lh
        col = p['red'] if sign == '-' else p['grn'] if sign == '+' else p['ink3']
        if scan:
            t0 = scan[0] + scan[1] * k
            bar = a([((0, t0), 'opacity:0'), ((t0 + .1, t0 + scan[1]), 'opacity:1'), ((t0 + scan[1] + .1, ST), 'opacity:0')], base='opacity:0;')
            s.add(f'<g class="{bar}"><rect x="{x}" y="{yy}" width="{w}" height="{lh}" fill="{p["tint"]}"/>'
                  f'<rect x="{x}" y="{yy}" width="3" height="{lh}" fill="{p["acc"]}"/></g>')
            if tick_col:
                tk = a.show(t0 + scan[1] * .6, dy=0, extra=' scale(.5)')
                s.add(f'<g class="{tk}" style="transform-box:fill-box;transform-origin:center">{check(x + w - (22 if ph else 34), yy + lh / 2, .7 if ph else 1, tick_col, 2)}</g>')
        T(s, x + 12, yy + lh / 2 + ms * .35, sign, 'pm500', col, ms)
        T(s, x + 12 + ms * 1.3, yy + lh / 2 + ms * .35, code, 'pm400', p['ink'] if sign != ' ' else p['ink2'], ms)
    bottom = y + hh + 10 + len(lines) * lh + 10
    box(s, x, y, w, bottom - y, p['ink3'], rx=2)
    return bottom


def scene_self_review(p, v):
    ph = v == 'phone'
    W = 308 if ph else 846
    s = Svg(W, 0, 'The server worker reads its own diff against its brief, line by line; a single counter goes from 0 to 5 '
                  'lines checked, then it is ready for review. All four self-reviews pass.')
    a = Anim(s, ST)
    t0, step = .8, .7
    dw = W if ph else 560
    bottom = diff_panel(s, a, 0, 0, dw, p, ph, DIFF, (t0, step), tick_col=p['ink2'])
    done_t = t0 + step * len(DIFF) + .2
    fs = 15 if ph else 18.5
    x, y = (0, bottom + 34) if ph else (600, 30)
    T(s, x, y, 'server', 'pm500', p['ink'], 14 if ph else 18.5)
    end = s.text(x + (62 if ph else 0), y + (0 if ph else 30), wrap([('reads its diff against its brief', 'nr400i', p['ink3'])], fs, (W - 62) if ph else W - x), fs, lh=24)
    y2 = end + (34 if ph else 48)
    T(s, x, y2, 'lines checked', 'nr400i', p['ink2'], fs)
    # One counter state at a time: each fades out before the next fades in; only the final state is in the static image.
    n = len(DIFF)
    for k in range(n + 1):
        tk = t0 + step * (k - 1) + .4
        if k == 0:
            c = a([((0, t0 + .4), 'opacity:1'), ((t0 + .42, ST), 'opacity:0')], base='opacity:0;')
        elif k < n:
            c = a([((0, tk + .02), 'opacity:0'), ((tk + .05, tk + step), 'opacity:1'), ((tk + step + .02, ST), 'opacity:0')], base='opacity:0;')
        else:
            c = a([((0, tk + .02), 'opacity:0'), ((tk + .05, ST - .8), 'opacity:1'), ((ST - .4, ST), 'opacity:0')])
        T(s, x + (W - x if ph else 246), y2, f'{k} / {n}', 'pm500', p['ink'], fs, anchor='end', cls=c)
    y3 = y2 + (40 if ph else 60)
    g = a.show(done_t, dy=0, extra=' scale(.9)')
    s.add(f'<g class="{g}" style="transform-box:fill-box;transform-origin:left center">')
    s.add(f'<circle cx="{x + 14}" cy="{y3 - 7}" r="14" fill="{p["acc"]}"/>' + check(x + 7.5, y3 - 7, .75, p['bg'], 2.4))
    T(s, x + 38, y3, 'ready for review', 'nr600', p['acc'], 17 if ph else 21)
    s.add('</g>')
    y4 = y3 + (32 if ph else 44)
    T(s, x, y4, 'all 4 self-reviews pass', 'nr400i', p['ink2'], fs, cls=a.show(done_t + .5))
    s.h = (y4 + 12) if ph else max(bottom, y4 + 12) + 4
    return s


FIX = [('+', 'challenges.delete(user)'), ('+', "test('replay is rejected')")]


def scene_cross(p, v):
    ph = v == 'phone'
    W = 308 if ph else 846
    s = Svg(W, 0, 'A reviewer from another model family reads the server diff and finds one blocking bug every self-review missed: '
                  'the challenge is never deleted, so replaying the same signed assertion signs in again. A worker deletes it on '
                  'first use and adds the test "replay is rejected", which goes red, then green. 0 blocking after one round.')
    a = Anim(s, ST)
    fs = 15 if ph else 18.5
    box(s, 0, 0, 230 if ph else 300, 34 if ph else 40, p['acc'], sw=1.3, rx=17 if ph else 20)
    s.add(f'<circle cx="17" cy="{17 if ph else 20}" r="5" fill="{p["acc"]}"/>')
    T(s, 32, 22 if ph else 27, 'reviewer', 'pm500', p['acc'], 13 if ph else 18.5)
    T(s, 104 if ph else 136, 22 if ph else 27, 'other model family', 'nr400i', p['ink2'], 14 if ph else 18.5)
    dw = W if ph else 470
    top = 56 if ph else 66
    scan = (.4, .4)
    bottom = diff_panel(s, a, 0, top, dw, p, ph, DIFF, scan)
    ms = 12.5 if ph else 18.5
    lh = 28 if ph else 38
    hh = 30 if ph else 42
    # The gap the reviewer flags: nothing consumes the challenge between reading it and verifying with it.
    gy = top + hh + 10 + 2 * lh
    gap = a([((0, 2.5), 'opacity:0'), ((2.7, 4.2), 'opacity:1'), ((4.4, ST), 'opacity:0')], base='opacity:0;')
    s.add(f'<g class="{gap}"><line x1="2" y1="{gy}" x2="{dw - 2}" y2="{gy}" stroke="{p["red"]}" stroke-width="2" stroke-dasharray="5 4"/>'
          f'<circle cx="6" cy="{gy}" r="4" fill="{p["red"]}"/></g>')
    # The fix, by the server worker.
    fy = bottom + (30 if ph else 40)
    fx = a.show(4.3, dy=-6)
    s.add(f'<g class="{fx}">')
    T(s, 0, fy, 'fix', 'pm500', p['ink'], 14 if ph else 18.5)
    T(s, 36 if ph else 50, fy, 'by the server worker', 'nr400i', p['ink3'], fs)
    py = fy + 12
    for k, (sign, code) in enumerate(FIX):
        yy = py + k * (lh + 4)
        s.add(f'<rect x="0" y="{yy}" width="{dw}" height="{lh}" rx="2" fill="{p["tint"]}"/>')
        T(s, 12, yy + lh / 2 + ms * .35, sign, 'pm500', p['grn'], ms)
        T(s, 12 + ms * 1.3, yy + lh / 2 + ms * .35, code, 'pm400', p['ink'], ms)
    s.add('</g>')
    left_end = py + 2 * (lh + 4)
    x, y, cw = (0, left_end + 40, W) if ph else (510, 26, W - 510)
    T(s, x, y, 'finding', 'nr400i', p['ink3'], fs)
    y += 14
    f1 = a.show(2.8, dx=0 if ph else 10, dy=6 if ph else 0)
    s.add(f'<g class="{f1}">')
    pad = 14
    T(s, x + pad, y + (26 if ph else 32), 'blocking', 'pm500', p['red'], 13 if ph else 18.5)
    end = s.text(x + pad, y + (52 if ph else 66), wrap([('A used challenge is never deleted.', 'nr600', p['ink'])], fs + 1, cw - 2 * pad), fs + 1, lh=(fs + 1) * 1.3)
    end = s.text(x + pad, end + (26 if ph else 32), wrap([('trigger: ', 'pm400', p['ink3']), ('replay the same signed assertion; it signs in again', 'nr400i', p['ink2'])], fs, cw - 2 * pad), fs, lh=fs * 1.35)
    end = s.text(x + pad, end + (26 if ph else 32), wrap([('missed by all 4 self-reviews', 'nr400i', p['ink3'])], fs, cw - 2 * pad), fs, lh=fs * 1.35)
    fh = end - y + (16 if ph else 20)
    box(s, x, y, cw, fh, p['red'], sw=1.3)
    strike = a([((0, 5.8), 'opacity:0'), ((6.0, ST - .8), 'opacity:1'), ((ST - .4, ST), 'opacity:0')])
    tw_ = 96 if ph else 106
    s.add(f'<g class="{strike}"><path d="M{x + cw - tw_ - 10} {y + 10}h{tw_}v{24 if ph else 28}h-{tw_}z" fill="{p["bg"]}" stroke="{p["grn"]}" stroke-width="1.2"/>'
          f'{check(x + cw - tw_, y + (22 if ph else 24), .7, p["grn"], 2)}</g>')
    T(s, x + cw - tw_ + 22, y + (27 if ph else 30), 'fixed', 'pm500', p['grn'], 13 if ph else 18.5, cls=strike)
    s.add('</g>')
    # The new test: red first, then green; the static image keeps the green one.
    y += fh + (22 if ph else 28)
    chh = 36 if ph else 50
    tsz = 13.5 if ph else 18.5
    red = a([((0, 4.8), 'opacity:0'), ((5.0, 5.5), 'opacity:1'), ((5.6, ST), 'opacity:0')], base='opacity:0;')
    grn = a([((0, 5.5), 'opacity:0'), ((5.6, ST - .8), 'opacity:1'), ((ST - .4, ST), 'opacity:0')])
    for cls, col, mark, word in ((red, p['red'], cross, 'fails'), (grn, p['grn'], check, 'passes')):
        s.add(f'<g class="{cls}">')
        box(s, x, y, cw, chh, col, sw=1.4)
        s.add(mark(x + 12, y + chh / 2, .8 if ph else 1, col, 2.2))
        T(s, x + (32 if ph else 40), y + chh / 2 + tsz * .35, "replay is rejected", 'pm500', p['ink'], tsz)
        T(s, x + cw - 12, y + chh / 2 + tsz * .35, word, 'nr600', col, 14 if ph else 18.5, anchor='end')
        s.add('</g>')
    y += chh + (36 if ph else 46)
    res = a.show(6.2, dy=0, extra=' scale(.9)')
    s.add(f'<g class="{res}" style="transform-box:fill-box;transform-origin:left center">')
    s.add(f'<circle cx="{x + 14}" cy="{y - 8}" r="14" fill="{p["acc"]}"/>' + check(x + 7.5, y - 8, .75, p['bg'], 2.4))
    T(s, x + 38, y, '0 blocking', 'nr600', p['acc'], 18 if ph else 22)
    T(s, x + (136 if ph else 156), y, '\u00b7 one round', 'nr400i', p['ink2'], fs)
    s.add('</g>')
    s.h = max(y + 16, left_end + 8)
    return s


def thumb(s, x, y, w, h, p, k):
    """A login screen: two fields and the blue passkey button."""
    box(s, x, y, w, h, p['ink3'], rx=2)
    fw = w - 2 * k * 8
    s.add(f'<rect x="{x + 8 * k:.1f}" y="{y + h * .18:.1f}" width="{fw:.1f}" height="{h * .14:.1f}" rx="1.5" fill="none" stroke="{p["rule"]}"/>'
          f'<rect x="{x + 8 * k:.1f}" y="{y + h * .4:.1f}" width="{fw:.1f}" height="{h * .14:.1f}" rx="1.5" fill="none" stroke="{p["rule"]}"/>'
          f'<rect x="{x + 8 * k:.1f}" y="{y + h * .64:.1f}" width="{fw:.1f}" height="{h * .18:.1f}" rx="1.5" fill="{p["acc"]}"/>')


def scene_done(p, v):
    ph = v == 'phone'
    W = 308 if ph else 846
    s = Svg(W, 0, 'Done: an evidence bundle assembles. Tests: 128 passed, 0 failed, in Chromium and WebKit. Screenshots of the '
                  'login screen with the passkey button at 390 and 1440. The pull request "Add passkey login": checks pass, '
                  'review found 1 blocking, fixed.')
    a = Anim(s, ST)
    fs = 15 if ph else 18.5
    bx, by, bw = (0, 120, W) if ph else (380, 0, W - 380)
    cx, cy = (54, 52) if ph else (150, 170)
    hh = 44 if ph else 52
    rows = [96, 120, 104] if ph else [108, 132, 118]
    bh = hh + sum(rows) + 12
    s.add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{hh}" fill="{p["tint"]}"/>')
    box(s, bx, by, bw, bh, p['ink3'], sw=1.2)
    T(s, bx + 16, by + hh / 2 + fs * .35, 'evidence', 'nr400i', p['ink2'], fs)
    cnt = [a([((0, 1.2 + .6 * k + .5), 'opacity:0'), ((1.2 + .6 * k + .55, (1.2 + .6 * (k + 1) + .5) if k < 2 else ST - .8), 'opacity:1'),
              (((1.2 + .6 * (k + 1) + .55) if k < 2 else ST - .4, ST), 'opacity:0')], base='opacity:0;' if k < 2 else '') for k in range(3)]
    for k in range(3):
        T(s, bx + bw - 16, by + hh / 2 + fs * .35, f'{k + 1} of 3', 'pm400', p['ink3'], 13 if ph else 18.5, anchor='end', cls=cnt[k])
    y = by + hh + 6
    ls_ = 13 if ph else 18.5
    for k, name in enumerate(['tests', 'screenshots', 'pull request']):
        rh = rows[k]
        dx, dy = (0, -80 - k * 30) if ph else (-360, 0)
        g = a([((0, 1.2 + .6 * k), f'opacity:0;transform:translate({dx}px,{dy}px) rotate(-3deg);{EASE}'),
               ((1.75 + .6 * k, ST - .8), 'opacity:1;transform:none'), ((ST - .4, ST), 'opacity:0;transform:none')])
        s.add(f'<g class="{g}" style="transform-box:fill-box;transform-origin:center">')
        ix, iw = bx + 12, bw - 24
        box(s, ix, y + 6, iw, rh - 12, p['rule'], fill=p['bg'], sw=1)
        T(s, ix + 14, y + 6 + (24 if ph else 30), name, 'nr400i', p['ink3'], ls_)
        ty = y + 6 + (50 if ph else 64)
        if k == 0:
            s.add(check(ix + 14, ty - 6, .7, p['grn'], 2))
            T(s, ix + 36, ty, '128 passed, 0 failed', 'pm500', p['ink'], 13.5 if ph else 18.5)
            if ph:
                T(s, ix + 36, ty + 22, 'Chromium \u00b7 WebKit', 'nr400i', p['ink2'], 14)
            else:
                T(s, ix + iw - 14, ty, 'Chromium \u00b7 WebKit', 'nr400i', p['ink2'], 18.5, anchor='end')
        elif k == 1:
            s.text(ix + 14, ty, wrap([('login, with the passkey button', 'nr400', p['ink'])], 14 if ph else 18.5, iw - (150 if ph else 210)), 14 if ph else 18.5, lh=20)
            th = rh - (48 if ph else 52)
            dw_, pw_ = (78, 30) if ph else (112, 42)
            dxx = ix + iw - 14 - dw_
            pxx = dxx - 14 - pw_
            thumb(s, pxx, y + 14, pw_, th, p, .5)
            thumb(s, dxx, y + 14, dw_, th, p, 1.4)
            T(s, pxx + pw_ / 2, y + 14 + th + (18 if ph else 22), '390', 'pm400', p['ink3'], 12.5 if ph else 18.5, anchor='middle')
            T(s, dxx + dw_ / 2, y + 14 + th + (18 if ph else 22), '1440', 'pm400', p['ink3'], 12.5 if ph else 18.5, anchor='middle')
        else:
            T(s, ix + 14, ty, 'Add passkey login', 'nr600', p['ink'], 14.5 if ph else 19)
            T(s, ix + iw - 14, ty, 'checks pass', 'nr400i', p['grn'], 14 if ph else 18.5, anchor='end')
            T(s, ix + 14, ty + (24 if ph else 30), 'review: 1 blocking found, fixed', 'nr400i', p['ink2'], 14 if ph else 18.5)
        s.add('</g>')
        y += rh
    pop = a([((0, 3.4), f'opacity:0;transform:scale(.6);{EASE}'), ((3.8, ST - .8), 'opacity:1;transform:none'), ((ST - .4, ST), 'opacity:0;transform:none')])
    r = 40 if ph else 72
    ring = a([((0, 3.5), 'opacity:0;transform:scale(1)'), (3.55, 'opacity:.5;transform:scale(1)'), ((4.4, ST), 'opacity:0;transform:scale(1.5)')],
             base='opacity:0;transform-box:fill-box;transform-origin:center;')
    s.add(f'<circle class="{ring}" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{p["acc"]}" stroke-width="2"/>')
    s.add(f'<g class="{pop}" style="transform-box:fill-box;transform-origin:center"><circle cx="{cx}" cy="{cy}" r="{r}" fill="{p["acc"]}"/>'
          f'{check(cx - r * .42, cy + r * .02, r / 26, p["bg"], r / 9)}</g>')
    lab = a.show(3.9)
    if ph:
        T(s, cx + r + 22, cy - 2, 'Done', 'nr600', p['ink'], 24, cls=lab)
        T(s, cx + r + 22, cy + 24, 'with evidence', 'nr400i', p['ink2'], 16, cls=lab)
    else:
        T(s, cx, cy + r + 50, 'Done', 'nr600', p['ink'], 30, anchor='middle', cls=lab)
        T(s, cx, cy + r + 80, 'with evidence', 'nr400i', p['ink2'], 20, anchor='middle', cls=lab)
    s.h = by + bh + 2
    return s


SCENES = {'you': scene_you, 'orchestrator': scene_orchestrator, 'workers': scene_workers,
          'self-review': scene_self_review, 'cross-model-review': scene_cross, 'done': scene_done}


def build():
    """Writes assets/agents/*.svg; returns the README section."""
    build_diagram()
    for i, (slug, _, _, _) in enumerate(STEPS):
        for theme, p in P.items():
            for v in ('desk', 'phone'):
                save(f'{OUT_ASSETS}/{slug}-sum-{v}-{theme}.svg', summary(p, v, i))
                save(f'{OUT_ASSETS}/{slug}-text-{v}-{theme}.svg', caption(p, v, i))
                save(f'{OUT_ASSETS}/{slug}-visual-{v}-{theme}.svg', SCENES[slug](p, v))
    return section_md()
