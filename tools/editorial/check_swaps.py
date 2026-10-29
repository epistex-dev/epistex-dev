#!/usr/bin/env python3
"""Fails when animated text sharing one position shows more or fewer than one state at a time.

Usage: python3 tools/editorial/check_swaps.py   (stdlib only; reads assets/agents)

A swap group is two or more <text> elements with the same x, y and anchor of which at least one is animated
(a counter that steps through its values, a label that is replaced by another). Effective opacity of a text is the
product of its own and its ancestors' opacity. Under prefers-reduced-motion the animation is off, so the base
opacity applies. Over the loop, opacity is interpolated linearly between keyframes and sampled every 0.05 s.
Reduced motion: the opacities of a group must add up to 1 (the one static state).
Loop: they never add up to more than 1 (no overlap), and between the first and the last moment they add up to 1 there is
no gap; the loop may start empty and fade out at its end.
Final frame: the loop holds its complete state until FINAL of the cycle, then fades out. Under reduced motion every
element is in that complete state: whatever is visible at FINAL is visible, and a swap group shows the state that is
showing at FINAL.
"""
import glob, os, re, sys
import xml.etree.ElementTree as ET

SVG = '{http://www.w3.org/2000/svg}'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTS = os.path.join(ROOT, 'assets', 'agents')
STEP_S = 0.05
FINAL = 0.89  # fraction of the cycle inside the closing hold: after the last build step, before the fade-out
TOL = 0.02  # keyframe percentages are rounded to 0.01%, which skews a 0.05 s cross-fade by up to 0.016
RULE = re.compile(r'\.(\w+)\{([^{}]*)\}')
KEYFRAMES = re.compile(r'@keyframes (\w+)\{((?:[^{}]*\{[^{}]*\})*)\}')
FRAME = re.compile(r'([\d.%,]+)\{([^}]*)\}')


def opacity_of(css, default=None):
    m = re.search(r'(?:^|;)opacity:([\d.]+)', css)
    return float(m.group(1)) if m else default


def parse_css(css):
    """-> (class -> (base opacity or None, keyframes name or None, duration s), keyframes name -> [(fraction, opacity)])"""
    frames = {}
    for name, body in KEYFRAMES.findall(css):
        pts = []
        for sels, decl in FRAME.findall(body):
            o = opacity_of(decl)
            if o is not None:
                pts += [(float(s.rstrip('%')) / 100, o) for s in sels.split(',')]
        frames[name] = sorted(pts)
    classes = {}
    for cls, decl in RULE.findall(KEYFRAMES.sub('', re.sub(r'@media[^{]*\{\*\{[^}]*\}\}', '', css))):
        anim = re.search(r'animation:(\w+) ([\d.]+)s', decl)
        classes[cls] = (opacity_of(decl), anim.group(1) if anim else None, float(anim.group(2)) if anim else 0.0)
    return classes, frames


def interpolate(pts, f, base):
    if not pts:
        return base
    if f <= pts[0][0]:
        return pts[0][1] if pts[0][0] > 0 or f == pts[0][0] else base
    for (f0, o0), (f1, o1) in zip(pts, pts[1:]):
        if f0 <= f <= f1:
            return o0 if f1 == f0 else o0 + (o1 - o0) * (f - f0) / (f1 - f0)
    return pts[-1][1]


def groups(path):
    """-> ({(x, y, anchor): [effective opacity function of time or None for static]}, loop seconds); time None = reduced motion."""
    root = ET.parse(path).getroot()
    css = ''.join(e.text or '' for e in root.iter(SVG + 'style'))
    classes, frames = parse_css(css)
    parent = {c: p for p in root.iter() for c in p}
    found, loop = {}, 0.0
    for t in root.iter(SVG + 'text'):
        chain, node = [], t
        while node is not None:
            chain += [classes[c] for c in (node.get('class') or '').split() if c in classes]
            node = parent.get(node)

        def at(time, chain=chain):
            o = 1.0
            for base, name, dur in chain:
                b = 1.0 if base is None else base
                o *= b if time is None or not name else interpolate(frames[name], (time % dur) / dur, b)
            return o
        found.setdefault((t.get('x'), t.get('y'), t.get('text-anchor')), []).append((at, any(c[1] for c in chain)))
        loop = max([loop] + [c[2] for c in chain])
    return {k: v for k, v in found.items() if len(v) > 1 and any(a for _, a in v)}, loop


def finals(path):
    """Yield (tag, class, final opacity, reduced-motion opacity) for every animated element."""
    root = ET.parse(path).getroot()
    classes, frames = parse_css(''.join(e.text or '' for e in root.iter(SVG + 'style')))
    parent = {c: p for p in root.iter() for c in p}
    for el in root.iter():
        own = [c for c in (el.get('class') or '').split() if c in classes and classes[c][1]]
        if not own:
            continue
        final = reduced = 1.0
        node = el
        while node is not None:
            for c in (node.get('class') or '').split():
                if c in classes:
                    base, name, dur = classes[c]
                    b = 1.0 if base is None else base
                    reduced *= b
                    final *= interpolate(frames[name], FINAL, b) if name else b
            node = parent.get(node)
        yield el.tag.replace(SVG, ''), ' '.join(own), final, reduced


def check(path):
    """Yield (position, moment, opacities) for every moment at which a swap group does not show exactly one state."""
    swaps, loop = groups(path)
    for pos, members in sorted(swaps.items()):
        ops = [at(None) for at, _ in members]
        if abs(sum(ops) - 1) > TOL:
            yield pos, None, ops
        moments = [k * STEP_S for k in range(int(round(loop / STEP_S)))]
        rows = [(m, [at(m) for at, _ in members]) for m in moments]
        full = [m for m, ops in rows if abs(sum(ops) - 1) <= TOL]
        for m, ops in rows:
            if sum(ops) > 1 + TOL or (full and full[0] <= m <= full[-1] and abs(sum(ops) - 1) > TOL):
                yield pos, m, ops
                break


def main():
    failed = checked = 0
    for path in sorted(glob.glob(os.path.join(AGENTS, '*.svg'))):
        for tag, cls, final, reduced in finals(path):
            checked += 1
            if abs(final - reduced) > TOL:
                print(f'FAIL {os.path.basename(path)} <{tag} class="{cls}">: reduced motion shows opacity {reduced:g}, '
                      f'the final frame has {final:g}')
                failed += 1
        swaps, _ = groups(path)
        checked += len(swaps)
        for pos, m, ops in check(path):
            when = 'reduced motion' if m is None else f'{m:.2f}s'
            print(f'FAIL {os.path.basename(path)} text at x={pos[0]} y={pos[1]}: at {when} the states have opacity '
                  f'{[round(o, 2) for o in ops]}, they must show exactly one state')
            failed += 1
    print(f'{checked} animated elements and swap groups, {failed} failing')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
