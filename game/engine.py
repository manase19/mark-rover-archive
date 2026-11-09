"""engine.py - the reusable core. Nothing in here knows about the story.

  * math, color and noise helpers
  * screen, pens and pixel-art primitives (rect, disc, layer, ect)
  * effects: wipe, fade_text, type_lines, tween
  * the wind/sand storm overlay and the HUD bars
  * Scene and Game: tiny framework chapters plug into

add a chaptr: subclass "Scene", add it with game.add(name, scene), and
move to it with game.go(name). See opening.py for a full example.
"""
import math
import random
import time
import turtle

from config import (COLS, DIM, H, HUD_FONT, INK, MAX_GRAINS, MSG_FONT, OCHRE, P,
                    STORM_TICK_MS, W, WORLD)


# ============================================================
# maths, colour and noise


def q(v):
    return int(v // P) * P


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return t * t * (3 - 2 * t)


def interp(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]

    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / max(1, x1 - x0)

    return pts[-1][1]


def _rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, t):
    a, b = _rgb(c1), _rgb(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(stops, n):
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(stops) - 1)
        k = min(int(t), len(stops) - 2)
        out.append(mix(stops[k], stops[k + 1], t - k))

    return out


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def clock_text(mins):
    m = int(mins) % 1440
    return "%02d:%02d" % (m // 60, m % 60)


def rnd(n):
    # use a hash instead of random so the same part of the world always
    # looks the same, even when it gets drawn again.
    n = (n * 374761393 + 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def smooth(x, seed, step):
    cells = WORLD // step
    i, f = (x // step) % cells, (x % step) / step
    f = f * f * (3 - 2 * f)

    # interpolate between two random points to avoid getting completely
    # random heights at every position. the modulo makes the noise repeat
    # when the player completes a full turn.
    a, b = rnd(i * 977 + seed), rnd(((i + 1) % cells) * 977 + seed)
    return a + (b - a) * f


def terrain(x, seed, step=10):
    return (0.7 * smooth(x, seed, step)
            + 0.3 * smooth(x, seed + 31, max(step // 2, 1)))


# ============================================================
# screen and pens

screen = turtle.Screen()
screen.setup(W, H)
screen.title("MARS-OPS // SENSORY LOG")
screen.bgcolor("black")
screen.tracer(0, 0)  # update the screen manually when we're ready to draw


def _make_pen():
    t = turtle.Turtle(visible=False)
    t.penup()
    t.speed(0)
    t.setundobuffer(None)
    return t


pen = _make_pen()    # the world
ui = _make_pen()     # hud
wind = _make_pen()   # storm
fx = _make_pen()     # transitions
txt = _make_pen()    # text and overlays

# only the world moves up and down when the camera bobs.
view = {"dy": 0}


# ============================================================
# drawing primitives


def rect(t, x, y, w, h, color):
    if t is pen:
        y += view["dy"]

    t.fillcolor(color)
    t.goto(x, y)
    t.begin_fill()
    t.goto(x + w, y)
    t.goto(x + w, y + h)
    t.goto(x, y + h)
    t.goto(x, y)
    t.end_fill()


def disc(cx, cy, r, color, floor=-999):
    for dy in range(-r, r + 1):
        y = cy + dy * P
        if y >= floor:
            half = int((r * r + r - dy * dy) ** 0.5)
            rect(pen, cx - half * P, y, (2 * half + 1) * P, P, color)


def bands(stops, top, n, h):
    for i, c in enumerate(gradient(stops, n)):
        rect(pen, -400, top - (i + 1) * h, W, h, c)


def layer(tops, c_top, c_body, lit=0, floor=-300):
    i = 0
    while i < COLS:
        # combine neighbouring columns with the same height into one
        # rectangle instead of drawing each column separately.
        j = i
        while j + 1 < COLS and tops[j + 1] == tops[i]:
            j += 1

        x, w, top = -400 + i * P, (j - i + 1) * P, tops[i]

        if top > floor:
            if top - lit > floor:
                rect(pen, x, floor, w, top - lit - floor, c_body)

            if lit:
                rect(pen, x, max(floor, top - lit), w, min(lit, top - floor), c_top)

        i = j + 1


def contours(tops, offsets, color, floor, h=3):
    for off in offsets:
        i = 0
        while i < COLS:
            y = tops[i] - off

            if y <= floor:
                i += 1
                continue

            j = i
            while j + 1 < COLS and tops[j + 1] - off == y:
                j += 1

            rect(pen, -400 + i * P, y, (j - i + 1) * P, h, color)
            i = j + 1


def puff(x, y, w, c1="#dcb496", c2="#e8c8aa"):
    rect(pen, x, y, w, 4, c1)
    rect(pen, x + 10, y + 4, max(4, w - 22), 4, c2)
    rect(pen, x + 4, y - 4, max(4, w - 18), 4, c1)


# ============================================================
# effects


def wipe(done, bars=15, step_ms=35):
    bh = H // bars

    def tick(i=0):
        if i < bars:
            rect(fx, -400, 300 - (i + 1) * bh, W, bh + 1, "black")
            screen.update()
            screen.ontimer(lambda: tick(i + 1), step_ms)
        else:
            done()

    tick()


def fade_text(lines, y, font, fg, done=None, fade_out=False, step_ms=140, steps=8):
    colors = gradient(["#000000", fg], steps)

    if fade_out:
        colors.reverse()

    def tick(i=0):
        if i < len(colors):
            txt.clear()
            txt.color(colors[i])

            for k, line in enumerate(lines):
                txt.goto(0, y - k * 30)
                txt.write(line, align="center", font=font)

            screen.update()
            screen.ontimer(lambda: tick(i + 1), step_ms)

        else:
            if fade_out:
                txt.clear()
                screen.update()

            if done:
                done()

    tick()


def type_lines(lines, x, y, font, color, done, speed=30, gap=400, line_h=26):
    pos = [0, 0]  # [current line, number of characters shown]
    txt.color(color)

    def tick():
        li, ci = pos
        txt.clear()

        for k in range(min(li, len(lines))):
            txt.goto(x, y - k * line_h)
            txt.write(lines[k], font=font)

        if li >= len(lines):
            screen.update()
            done()
            return

        ci += 1
        txt.goto(x, y - li * line_h)
        txt.write(lines[li][:ci] + "_", font=font)
        screen.update()

        if ci >= len(lines[li]):
            pos[0], pos[1] = li + 1, 0
            screen.ontimer(tick, gap)
        else:
            pos[1] = ci
            screen.ontimer(tick, speed)

    tick()


def tween(seconds, on_frame, done=None):
    # use actual elapsed time instead of counting frames, so the animation
    # still takes the same amount of time even if the computer runs slowly.
    t0 = time.monotonic()

    def frame():
        elapsed = time.monotonic() - t0
        p = min(1.0, elapsed / seconds)

        on_frame(p, elapsed)

        if p < 1.0:
            screen.ontimer(frame, 1)
        elif done:
            done()

    frame()


# ============================================================
# wind and sand storm

_grains = []
_grains_key = [None]


def _new_grain(cfg, x=None):
    return [random.uniform(-400, 400) if x is None else x,
            max(cfg["ymin"], min(cfg["ymax"], random.gauss(cfg["ycenter"], cfg["yspread"]))),
            random.uniform(6, 18),
            random.choice((4, 4, 8)),
            random.randrange(4)]


def render_storm(cfg, tick):
    wind.clear()
    count = cfg.get("count", MAX_GRAINS)

    # only create a new set of grains when the storm key changes.
    # otherwise they would jump to random positions every time the scene redraws.
    if _grains_key[0] != cfg["key"]:
        _grains[:] = [_new_grain(cfg) for _ in range(count)]
        _grains_key[0] = cfg["key"]

    lo, hi = cfg["ymin"], cfg["ymax"]
    gust = 0.5 + 0.5 * math.sin(tick / 20.0)
    lvl = cfg["level"](gust)
    cols = cfg["colors"]

    for g in _grains[:int(count * lvl)]:
        g[0] += g[2] * (0.7 + 1.3 * gust)
        g[1] = max(lo, min(hi, g[1] + random.uniform(-2.5, 1.5)))

        if g[0] > 400:
            g[:] = _new_grain(cfg, -404)

        ln = g[3] * (2 if gust > 0.55 else 1)
        rect(wind, int(g[0] // 4) * 4, int(g[1] // 4) * 4, ln, 4, cols[g[4]])

    if gust > 0.4:
        span = max(40, hi - lo - 40)

        for k in range(int(cfg["streaks"] * lvl)):
            x = ((tick * 16 * (1 + k % 3) + k * 173) % 900) - 450
            y = lo + 20 + (k * 83) % span
            rect(wind, x, y, 48 + (k * 29) % 90, 2, cols[(k + 1) % 2])


# ============================================================
# hud


def draw_hud(info):
    ui.clear()
    rect(ui, -400, 268, W, 32, INK)
    rect(ui, -400, -300, W, 44, INK)
    rect(ui, -400, -258, W, 2, DIM)

    ui.color(OCHRE)

    for x, align, text in info.get("top", []):
        ui.goto(x, 274)
        ui.write(text, align=align, font=HUD_FONT)

    ui.goto(-388, -290)
    ui.write("> " + info.get("msg", ""), font=MSG_FONT)

    if info.get("hint"):
        rect(ui, -140, 234, 280, 24, INK)
        ui.color(OCHRE)
        ui.goto(0, 238)
        ui.write(info["hint"], align="center", font=HUD_FONT)


# ============================================================
# scenes and game


class Scene:
    hud = True

    def enter(self, game):
        pass

    def draw(self, game):
        pass

    def hud_info(self, game):
        return {}

    def storm(self, game):
        return None

    def on_click(self, game, x, y):
        pass

    def on_key(self, game, key):
        pass


class Game:
    def __init__(self):
        self.state = {"tick": 0}
        self.scenes = {}
        self.scene = None
        self.busy = True
        self.storm_on = False

    def add(self, name, scene):
        self.scenes[name] = scene
        return scene

    def go(self, name):
        self.scene = self.scenes[name]

        # clear anything left by the previous scene before starting the next one.
        fx.clear()
        txt.clear()
        ui.clear()
        view["dy"] = 0

        self.scene.enter(self)

    def after(self, ms, fn):
        screen.ontimer(fn, ms)

    def set_storm(self, on):
        self.storm_on = on
        if not on:
            wind.clear()

    def render(self):
        sc = self.scene
        pen.clear()
        sc.draw(self)

        if sc.hud:
            draw_hud(sc.hud_info(self))
        else:
            ui.clear()

        cfg = sc.storm(self) if self.storm_on else None
        if cfg:
            render_storm(cfg, self.state["tick"])

        screen.update()

    def refresh_hud(self):
        if self.scene and self.scene.hud:
            draw_hud(self.scene.hud_info(self))
            screen.update()

    def _click(self, x, y):
        if self.scene and not self.busy:
            self.scene.on_click(self, x, y)

    def _key(self, key):
        if self.scene and not self.busy:
            self.scene.on_key(self, key)

    def _storm_tick(self):
        cfg = self.scene.storm(self) if (self.storm_on and self.scene) else None

        if cfg:
            self.state["tick"] += 1
            render_storm(cfg, self.state["tick"])
            screen.update()

        # keep checking even when there's no active storm.
        screen.ontimer(self._storm_tick, STORM_TICK_MS)

    def start(self, first, keys=()):
        screen.onscreenclick(self._click)

        for k in keys:
            # k=k makes each key callback remember its own key instead of
            # all callbacks using the last key in the loop.
            screen.onkey(lambda k=k: self._key(k), k)

        screen.listen()
        screen.ontimer(self._storm_tick, STORM_TICK_MS)
        self.go(first)
        turtle.done()