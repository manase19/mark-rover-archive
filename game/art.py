import math

from config import COLS, P, WORLD
from engine import interp, lerp, mix, pen, q, rect, rnd

"""oyoyoyoyoyooyoyoyoyoyooyoyoyoyoyooyoyoyoyoyooyoyoyoyoyo
#DFS BFS DP DFS BFS DP DFS BFS DP DFS BFS DP DFS BFS DP
     @elgorithms"""
def X(i):
    return -400 + i * P


# ============================================================

def scol(wc, pan, margin=8):
    # wrap the world column around so objects on the other side can appear
    # just outside the screen instead of suddenly disappearing.
    sc = (wc - pan) % WORLD
    if sc > WORLD - margin:
        sc -= WORLD
    return sc if sc < COLS + margin else None


def heading(wc):
    return (wc + 180) % WORLD - 180


def sample(pan, zoom):
    # keep the zoom centred on the screen instead of shifting the whole view.
    mid = COLS // 2
    return [int(pan + mid + (c - mid) / zoom) % WORLD for c in range(COLS)]


def zoom_for(rate, travel, pan, fwd=0):
    # cosine decides whether we're facing towards or away from this layer.
    # this makes scenery grow as we approach it and shrink as we move away.
    facing = math.cos(math.radians((pan + COLS // 2 - fwd) % WORLD))
    return (1 + rate * travel) ** facing


def lerp_list(vals, t):
    i = min(int(t), len(vals) - 2)
    return lerp(vals[i], vals[i + 1], min(1.0, t - i))


# ============================================================
# ground details

# each rock or ripple has its own position and movement cycle.
# when it passes the viewer, it starts over with a new position.


def slot(key, travel, rate):
    u = rnd(key + 4) + travel * rate
    cyc = int(u)
    # keep the fractional part as the object's position within its cycle.
    return cyc, u - cyc


def rr(key, cyc, k):
    # using the same seed keeps an object looking the same between frames,
    # even though its position is calculated again every time.
    return rnd(key + k + cyc * 7919)


def draw_ripples(pal, pan, travel, seed, horizon, rate, reach=300, count=140):
    for i in range(count):
        key = seed + 3000 + i * 7
        cyc, p = slot(key, travel, rate)
        sc = scol(int(rr(key, cyc, 3) * WORLD), pan)
        if sc is None:
            continue

        d = p ** 1.5
        w = int((2 + rr(key, cyc, 5) * 4) * P * (1 + 2 * d))
        c = pal["streak"] if rr(key, cyc, 6) < 0.5 else pal["sand"]
        rect(pen, X(sc), q(horizon - 10 - d * reach), w, 3 + int(d * 5), c)


def draw_rocks(pal, pan, travel, seed, horizon, rate, reach=300, count=130, avoid=None):
    items = []
    for i in range(count):
        key = seed + 1000 + i * 13
        cyc, p = slot(key, travel, rate)
        sc = scol(int(rr(key, cyc, 1) * WORLD), pan, 6)

        if sc is None or (avoid is not None and abs(sc - avoid) < 15):
            continue

        d = p ** 1.5
        items.append((q(horizon - 8 - d * reach), X(sc), d, key, cyc))

    items.sort(reverse=True)
    for y, x, d, key, cyc in items:
        w = int(10 + d * 64)

        if rr(key, cyc, 3) < 0.55:
            h = 3 + int(d * 7)
            rect(pen, x, y, w, h, pal["rock_d"])
            rect(pen, x + 2, y + h - 2, w * 3 // 4, 2, pal["rock_l"])
        else:
            for k in range(3):
                pw = 4 + int(d * 8)
                rect(pen, x + k * (pw + 2), y + (k % 2) * 2, pw, max(3, pw // 2), pal["rock_d"])


# ============================================================
# cliffs and rock formations


def ridge(pts, seed=0, jag=0, run=(1, 3)):
    out, c = [], 0
    while c < COLS:
        n = run[0] + int(rnd(c * 31 + seed) * (run[1] - run[0] + 1))
        off = (rnd(c * 17 + seed + 5) - 0.5) * jag * 1.5

        # use the same offset across a short run of columns to create
        # blocky peaks instead of making every column completely random.
        for k in range(c, min(COLS, c + n)):
            out.append(q(interp(pts, k) + off))
        c += n

    return out[:COLS]


def _seam(i, j, y0, color, salt):
    c = i
    while c <= j:
        n = min(1 + int(rnd(salt + c * 13) * 4), j - c + 1)
        dip = 4 * int(rnd(salt + c * 13 + 1) * 3)
        rect(pen, X(c), y0 + dip, n * P, 3, color)
        c += n


def cliff_face(tops, floor, pal, seed=0, gullies=0, haze_h=0):
    top_max = max(tops)
    if top_max <= floor:
        return

    span = float(top_max - floor)

    def tone(ym, k):
        c = mix(pal["low"], pal["high"], (ym - floor) / span)
        c = mix(c, pal["dark"], 0.3) if k % 2 else mix(c, pal["lit"], 0.2)

        if haze_h and ym - floor < haze_h:
            c = mix(c, pal["haze"], 0.85 * (1 - (ym - floor) / haze_h))
        return c

    y, k = floor, 0
    while y < top_max:
        h = 4 * (4 + int(rnd(seed + k * 7) * 8))
        y0, y1 = y, y + h
        col = tone((y0 + y1) / 2.0, k)
        seam = mix(col, pal["seam"], 0.65)

        i = 0
        while i < COLS:
            if tops[i] >= y1:
                # group neighbouring columns with enough height so we can
                # draw one large rectangle instead of drawing every column.
                j = i
                while j + 1 < COLS and tops[j + 1] >= y1:
                    j += 1

                rect(pen, X(i), y0, (j - i + 1) * P, h, col)
                _seam(i, j, y0, seam, seed * 101 + k * 17)
                i = j + 1

            elif y0 < tops[i] < y1:
                j = i
                while j + 1 < COLS and tops[j + 1] == tops[i]:
                    j += 1

                rect(pen, X(i), y0, (j - i + 1) * P, tops[i] - y0, col)
                rect(pen, X(i), y0, (j - i + 1) * P, 3, seam)
                i = j + 1

            else:
                i += 1

        y, k = y1, k + 1

    i = 0
    while i < COLS:
        j = i
        while j + 1 < COLS and tops[j + 1] == tops[i]:
            j += 1

        if tops[i] > floor:
            cap = min(P * 2, tops[i] - floor)
            rect(pen, X(i), tops[i] - cap, (j - i + 1) * P, cap, pal["crest"])

        i = j + 1

    # the light comes from the right, so the two sides of a height change
    # need different shades to make the cliff look less flat.
    for i in range(COLS):
        t = tops[i]
        if t <= floor:
            continue

        right = tops[i + 1] if i + 1 < COLS else t
        left = tops[i - 1] if i else t

        if t - right >= P:
            b = max(right, floor)
            rect(pen, X(i) + P - 4, b, 4, t - b, pal["lit"])

        if t - left >= P:
            b = max(left, floor)
            rect(pen, X(i), b, 6, t - b, pal["dark"])


def chunk(x, y, w, h, cols, seed=0):
    light, mid, dark, shadow = cols

    rect(pen, x - 8, y - 4, w + 16, 4, shadow)

    rows = max(4, h // 4)

    cut_l = 0.15 + 0.30 * rnd(seed)
    cut_r = 0.15 + 0.40 * rnd(seed + 1)

    split_base = 0.4 + 0.3 * rnd(seed + 2)

    for r in range(rows):
        t = r / float(rows - 1)

        inset_l = int(w * cut_l * max(0.0, t - 0.2)) // 4 * 4
        inset_r = int(w * cut_r * max(0.0, t - 0.4)) // 4 * 4

        left, right = x + inset_l, x + w - inset_r

        # move the split slightly in each row so the boulder has
        # irregular faces instead of two perfectly straight halves.
        fracture = (rnd(seed + r) - 0.5) * 0.2
        facet = x + int(w * (split_base + fracture - 0.1 * t)) // 4 * 4
        facet = max(left + 4, min(right - 4, facet))

        top_row = r >= rows - 2
        rect(pen, left, y + r * 4, facet - left, 4, mid if top_row else dark)
        rect(pen, facet, y + r * 4, right - facet, 4, light if top_row else mid)