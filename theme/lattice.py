"""The network lattice: a port of aljulandani.dev's scripts/backdrops.mjs.

A jittered 3D grid of lines along the three axes of a tilted box, seen in
perspective, strung with beads of three sizes; some lines carry travelling
beads. The same seeded generator (mulberry32, seeds 7 and 31) as the site, so
the desktop draws the same lattice as the portfolio.

    from lattice import lattice
    art = lattice()            # view box 1000 x 700
    art["lines"]   -> [(x1, y1, x2, y2, depth)]           depth: "f" | "m" | "n"
    art["beads"]   -> [(x1, y1, x2, y2, depth, kind, dasharray)]   kind: "s" | "md" | "b"
    art["packets"] -> [(x1, y1, x2, y2, depth, speed, phase)]      speed: 0-7, phase: 0-9
    svg_lines(art), svg_beads(art) -> SVG markup (stroke #000, alpha by depth: use as a mask or recolour)
"""
import math

W, H, F = 1000, 700, 1050                  # view box and focal length
OPACITY = {"f": 0.5, "m": 0.8, "n": 1.0}
SCALE = {"f": 0.6, "m": 1.0, "n": 1.6}
WIDTH = {"s": 2.2, "md": 4.0, "b": 7.0}


def r1(n):
    return math.floor(n * 10 + 0.5) / 10


def _imul(a, b):
    return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF


def _i32(x):
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x & 0x80000000 else x


def rng(seed):
    """mulberry32, bit-exact with the site's JavaScript."""
    state = [_i32(seed)]

    def nxt():
        state[0] = _i32(state[0] + 0x6D2B79F5)
        s = state[0] & 0xFFFFFFFF
        t = _imul(s ^ (s >> 15), 1 | s)
        t = (_i32(t + _imul(t ^ (t >> 7), 61 | t)) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return nxt


def lattice():
    rand = rng(7)
    pick = lambda a: a[int(rand() * len(a))]
    HALF, Z0, NEAR, STEP = [6.5, 4.5, 4.5], 9.5, 2.6, 1.1
    ya, pa, ra = 0.5, -0.38, 0.22

    def rot(p):
        x, y, z = p
        x, z = x * math.cos(ya) + z * math.sin(ya), -x * math.sin(ya) + z * math.cos(ya)
        y, z = y * math.cos(pa) - z * math.sin(pa), y * math.sin(pa) + z * math.cos(pa)
        x, y = x * math.cos(ra) - y * math.sin(ra), x * math.sin(ra) + y * math.cos(ra)
        return [x, y, z + Z0]

    project = lambda p: (W / 2 + F * p[0] / p[2], H / 2 + F * p[1] / p[2])
    lerp = lambda a, b, t: [v + (b[i] - v) * t for i, v in enumerate(a)]

    DEPTH = [("f", 0.6), ("m", 1.0), ("n", 1.6)]
    KINDS = {"s": (9, 4, 15), "md": (5, 12, 40), "b": (3, 35, 120)}
    patterns = {}
    for d, k in DEPTH:
        for kind, (dots, lo, hi) in KINDS.items():
            patterns[kind + d] = [" ".join(f"0 {r1((lo + rand() * (hi - lo)) * k):g}" for _ in range(dots))
                                  for _ in range(3)]

    lines3 = []
    for axis in range(3):
        a, b = [i for i in range(3) if i != axis]
        u = -HALF[a]
        while u <= HALF[a] + 1e-9:
            v = -HALF[b]
            while v <= HALF[b] + 1e-9:
                if rand() > 0.17:
                    v += STEP
                    continue
                twins = [0, 0.16] if rand() < 0.2 else [0]
                for off in twins:
                    p, q = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
                    p[a] = q[a] = u + (rand() - 0.5) * 0.3 + off
                    p[b] = q[b] = v + (rand() - 0.5) * 0.3
                    p[axis], q[axis] = -HALF[axis], HALF[axis]
                    lines3.append((rot(p), rot(q)))
                v += STEP
            u += STEP

    def depth(z):
        return 0 if Z0 / z < 0.85 else (1 if Z0 / z < 1.3 else 2)

    out_lines, out_beads, packets = [], [], []
    prand = rng(31)
    for p, q in lines3:
        if p[2] < NEAR and q[2] < NEAR:
            continue
        if p[2] < NEAR:
            p = lerp(p, q, (NEAR - p[2]) / (q[2] - p[2]))
        if q[2] < NEAR:
            q = lerp(q, p, (NEAR - q[2]) / (p[2] - q[2]))
        P, Q = project(p), project(q)
        if (max(P[0], Q[0]) < -100 or min(P[0], Q[0]) > W + 100
                or max(P[1], Q[1]) < -100 or min(P[1], Q[1]) > H + 100):
            continue
        dc = DEPTH[depth((p[2] + q[2]) / 2)][0]
        out_lines.append((r1(P[0]), r1(P[1]), r1(Q[0]), r1(Q[1]), dc))
        for i in range(3):
            a3, b3 = lerp(p, q, i / 3), lerp(p, q, (i + 1) / 3)
            dci = DEPTH[depth((a3[2] + b3[2]) / 2)][0]
            A, B = project(a3), project(b3)
            seg = (r1(A[0]), r1(A[1]), r1(B[0]), r1(B[1]))
            out_beads.append((*seg, dci, "s", pick(patterns["s" + dci])))
            if rand() < 0.85:
                out_beads.append((*seg, dci, "md", pick(patterns["md" + dci])))
            if rand() < 0.6:
                out_beads.append((*seg, dci, "b", pick(patterns["b" + dci])))
        if prand() < 0.4:
            packets.append(((P, Q), dc))

    dots = []
    for (P, Q), dc in packets:
        for _ in range(1 + int(prand() ** 2 * 5)):
            A, B = (Q, P) if prand() < 0.3 else (P, Q)
            dots.append((r1(A[0]), r1(A[1]), r1(B[0]), r1(B[1]), dc, int(prand() * 8), int(prand() * 10)))
    return {"lines": out_lines, "beads": out_beads, "packets": dots, "view": (W, H)}


def dash_points(x1, y1, x2, y2, dasharray):
    """Where a "0 g1 0 g2 ..." dash pattern with round caps puts its dots along a segment."""
    gaps = [float(v) for v in dasharray.split()][1::2]
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0 or not gaps or sum(gaps) <= 0:
        return []
    pts, s, i = [], 0.0, 0
    while s <= length:
        t = s / length
        pts.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
        s += gaps[i % len(gaps)]
        i += 1
    return pts


def svg_lines(art, colour="#000"):
    groups = {}
    for x1, y1, x2, y2, dc in art["lines"]:
        groups.setdefault(dc, []).append(f'<path d="M{x1:g} {y1:g}L{x2:g} {y2:g}"/>')
    body = "".join(f'<g stroke-opacity="{OPACITY[d]:g}" stroke-width="0.7">{"".join(p)}</g>' for d, p in groups.items())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'fill="none" stroke="{colour}">{body}</svg>')


def svg_beads(art, colour="#000"):
    groups = {}
    for x1, y1, x2, y2, dc, kind, dash in art["beads"]:
        groups.setdefault((kind, dc), []).append(f'<path stroke-dasharray="{dash}" d="M{x1:g} {y1:g}L{x2:g} {y2:g}"/>')
    body = "".join(f'<g stroke-opacity="{OPACITY[d]:g}" stroke-width="{r1(WIDTH[k] * SCALE[d]):g}" stroke-linecap="round">{"".join(p)}</g>'
                   for (k, d), p in groups.items())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'fill="none" stroke="{colour}">{body}</svg>')


if __name__ == "__main__":
    a = lattice()
    print(f"lines {len(a['lines'])}, bead strings {len(a['beads'])}, travelling beads {len(a['packets'])}")
