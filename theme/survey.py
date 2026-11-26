"""The survey field: the backdrop. A topographic map of a seeded height field.

Contour lines (isolines) of a smooth terrain, drawn as hairlines; every fifth one is an
index contour, a little brighter and strung with survey-station beads. Traces run along the
contours in the signal colour: a lit stretch of line, bright at its head and fading behind
it. The live version moves them; the still shows them where they stand at t = 0. Every
edition surveys its own terrain (its own seed, mulberry32 as in lattice.py), and each render
of an edition draws the same map. No text, ever.

    from survey import survey, svg_lines, svg_beads
    art = survey("amber")      # view box 1000 x 700
    art["lines"]   -> [(points, kind)]           kind: "minor" | "index"
    art["beads"]   -> [(x, y, size)]             survey stations on the index contours
    art["packets"] -> [(points, closed, speed, phase)]   traces; speed: 0-7, phase: 0-9
    svg_lines(art, colour), svg_beads(art, colour) -> SVG markup
"""
import math

from lattice import rng

W, H = 1000, 700
STEP = 8                     # grid spacing of the height field, in view-box units
LEVELS = 32                  # contour levels between the lowest and highest point
INDEX_EVERY = 5              # every fifth level is an index contour
OPACITY = {"minor": 0.6, "index": 1.0}
WIDTH = {"minor": 0.7, "index": 1.1}
BEAD_GAP = 46                # survey stations along the index contours


SEEDS = {"cyan": 19, "amber": 61, "phosphor": 23, "acid": 88, "hazard": 37, "mono": 74, "paper": 52, "lab": 95,
         "ice": 43, "chrome": 67, "slate": 29, "ruby": 81}   # the y2k editions survey their own land too


def _field(seed):
    """A smooth terrain: seeded hills and hollows on a gentle tilt."""
    rand = rng(seed)
    bumps = []
    for _ in range(16):
        bumps.append((rand() * W * 1.2 - W * 0.1, rand() * H * 1.2 - H * 0.1,
                      60 + rand() * 150, (rand() - 0.45) * 2.0))
    tilt = (rand() - 0.5) * 0.0006, (rand() - 0.5) * 0.0006

    def h(x, y):
        v = x * tilt[0] + y * tilt[1]
        for bx, by, r, a in bumps:
            v += a * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * r * r))
        return v
    return h


def _segments(grid, nx, ny, level):
    """Marching squares: the line segments where the field crosses `level`."""
    segs = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a, b = grid[j][i], grid[j][i + 1]
            c, d = grid[j + 1][i + 1], grid[j + 1][i]
            x0, y0 = i * STEP, j * STEP
            pts = []
            for (p, q, P, Q) in ((a, b, (x0, y0), (x0 + STEP, y0)),
                                 (b, c, (x0 + STEP, y0), (x0 + STEP, y0 + STEP)),
                                 (c, d, (x0 + STEP, y0 + STEP), (x0, y0 + STEP)),
                                 (d, a, (x0, y0 + STEP), (x0, y0))):
                if (p < level) != (q < level):
                    t = (level - p) / (q - p)
                    pts.append((P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t))
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
            elif len(pts) == 4:                      # a saddle: pair by the centre value
                centre = (a + b + c + d) / 4
                if (centre < level) == (a < level):
                    segs += [(pts[0], pts[3]), (pts[1], pts[2])]
                else:
                    segs += [(pts[0], pts[1]), (pts[2], pts[3])]
    return segs


def _join(segs):
    """Chain segments into polylines; returns [(points, closed)]."""
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    ends = {}
    for n, (p, q) in enumerate(segs):
        ends.setdefault(key(p), []).append((n, 0))
        ends.setdefault(key(q), []).append((n, 1))
    used = [False] * len(segs)
    out = []
    for n in range(len(segs)):
        if used[n]:
            continue
        used[n] = True
        line = [segs[n][0], segs[n][1]]
        for direction in (1, 0):                     # grow from the tail, then from the head
            while True:
                tip = line[-1] if direction else line[0]
                nxt = None
                for m, side in ends.get(key(tip), []):
                    if not used[m]:
                        nxt = (m, side)
                        break
                if nxt is None:
                    break
                m, side = nxt
                used[m] = True
                other = segs[m][1 - side]
                if direction:
                    line.append(other)
                else:
                    line.insert(0, other)
        closed = key(line[0]) == key(line[-1]) and len(line) > 3
        out.append((line, closed))
    return out


def _simplify(points, tol=0.6):
    """Drop points that sit on a straight run (keeps files small)."""
    if len(points) < 3:
        return points
    out = [points[0]]
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = out[-1], points[i], points[i + 1]
        area = abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
        if area > tol * math.hypot(x2 - x0, y2 - y0):
            out.append(points[i])
    out.append(points[-1])
    return out


def length(points):
    return sum(math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
               for i in range(len(points) - 1))


def walk(points, u):
    """The point a share u (0..1) of the way along a polyline."""
    total = length(points)
    target, run = u * total, 0.0
    for i in range(len(points) - 1):
        (x1, y1), (x2, y2) = points[i], points[i + 1]
        seg = math.hypot(x2 - x1, y2 - y1)
        if run + seg >= target and seg > 0:
            t = (target - run) / seg
            return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        run += seg
    return points[-1]


def survey(edition="cyan"):
    h = _field(SEEDS.get(edition, 19))
    nx, ny = W // STEP + 3, H // STEP + 3
    grid = [[h((i - 1) * STEP, (j - 1) * STEP) for i in range(nx)] for j in range(ny)]
    lo, hi = min(map(min, grid)), max(map(max, grid))
    lines, beads, routes = [], [], []
    prand = rng(SEEDS.get(edition, 19) + 24)
    for k in range(1, LEVELS):
        level = lo + (hi - lo) * k / LEVELS
        kind = "index" if k % INDEX_EVERY == 0 else "minor"
        for pts, closed in _join(_segments(grid, nx, ny, level)):
            pts = [(round(x - STEP, 1), round(y - STEP, 1)) for x, y in _simplify(pts)]
            if len(pts) < 2 or length(pts) < 24:
                continue
            lines.append((pts, kind))
            L = length(pts)
            if kind == "index":
                s = BEAD_GAP / 2
                while s < L:
                    x, y = walk(pts, s / L)
                    beads.append((round(x, 1), round(y, 1), 3.4 if int(s / BEAD_GAP) % 4 == 0 else 2.0))
                    s += BEAD_GAP
            if L > 180 and prand() < (0.7 if closed else 0.45):
                for _ in range(1 + int(prand() ** 2 * 3)):
                    routes.append((pts, closed, int(prand() * 8), int(prand() * 10)))
    return {"lines": lines, "beads": beads, "packets": routes, "view": (W, H)}


def _path(points):
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in points)


def svg_lines(art, colour="#000"):
    body = "".join(f'<g stroke-opacity="{OPACITY[k]:g}" stroke-width="{WIDTH[k]:g}">'
                   + "".join(f'<path d="{_path(p)}"/>' for p, kind in art["lines"] if kind == k) + "</g>"
                   for k in ("minor", "index"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'fill="none" stroke="{colour}" stroke-linejoin="round">{body}</svg>')


def svg_beads(art, colour="#000"):
    body = "".join(f'<circle cx="{x:g}" cy="{y:g}" r="{r / 2:g}"/>' for x, y, r in art["beads"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
            f'fill="{colour}">{body}</svg>')


if __name__ == "__main__":
    a = survey()
    print(f"contours {len(a['lines'])}, stations {len(a['beads'])}, packets {len(a['packets'])}")
