from art import (X, chunk, cliff_face, draw_ripples, draw_rocks, heading, lerp_list,
                 ridge, sample, scol, zoom_for)
from config import (AFTER_JUMP_MSG, BOB_PX, BOOT, CANYON, CANYON_PTS, CANYON_RUBBLE,
                    CLOCKS, COLS, DEPTH_PER_STEP, DIM, END_CARD, FACE_FORWARD_MSG,
                    FINAL_LINES, FONT, FORWARD_MSGS, FORWARD_PAN, HORIZON, JUMP_AT,
                    LANDER_COL, LANDER_U, LEG_METERS, LOOK_BACK_MSG, NO_LANDER_MSG,
                    TURN_BACK_HINT, TURN_BACK_MSG, OCHRE, P, PAL,
                    PAN_FRAMES, POST_JUMP_CLOCK, RIDGE_AT, RISE, SHOW_ODOMETER,
                    SLOPE_HALF, STRIDE_SECONDS, SUN_COL, TIMELAPSE_TEXT, TITLE,
                    TURNING_MSG, V_HORIZON, VISTA_MSG, WALK_MSG, WALK_SECONDS, WORLD)
from engine import (Scene, bands, clock_text, contours, disc, ease, fade_text, fx,
                    layer, lerp, minutes, pen, puff, q, rect, rnd, terrain, tween,
                    type_lines, txt, view, wipe)


# ============================================================
# shared hud


def top_bar(st):
    bar = [(-388, "left", TITLE),
           (0, "center", "HDG %03d" % ((st["pan"] + COLS // 2) % WORLD))]

    if SHOW_ODOMETER:
        bar.append((225, "right", "ODOM %04d m" % st["odo"]))

    bar.append((388, "right", "SOL 0001  " + clock_text(st["clock_min"])))
    return bar


# ============================================================
# the lander


def draw_trail(pal, cx, y0, u):
    bottom = -246
    y, k = bottom, 0

    while y < y0 - 2:
        # the footprints spread out as they get closer to the viewer.
        t = (y0 - y) / float(y0 - bottom)
        side = -1 if k % 2 else 1
        x = cx + side * int(2 * u * (1 - t) + 22 * t)
        w, h = 4 + int(8 * t), 3 + int(3 * t)

        rect(pen, x - w // 2, y, w, h, pal["streak"])
        y += 8 + int(22 * t)
        k += 1


def draw_lander(pal, sc, n):
    cx = X(sc)
    u = LANDER_U[n]
    y0 = min(HORIZON - 8, -150 + n * 38)
    sh = max(2, u // 2)
    metal, lit, dark, gold = "#8e8981", "#cfcac0", "#5b5650", "#c9a23e"

    draw_trail(pal, cx, y0, u)
    rect(pen, cx - 10 * u, y0 - sh, 21 * u, sh, pal["rock_d"])

    rect(pen, cx - 18 * u, y0, 7 * u, u, "#e8dcc6")
    rect(pen, cx - 17 * u, y0 + u, 4 * u, u, "#f2e8d4")
    rect(pen, cx - 15 * u, y0 + 2 * u, 2 * u, u, "#e8dcc6")

    for k in range(5):
        off = int((4 + 0.9 * k) * u)
        rect(pen, cx - off - u, y0 + (4 - k) * u, u, u, metal)
        rect(pen, cx + off, y0 + (4 - k) * u, u, u, dark)

    for s in (-1, 1):
        rect(pen, cx + s * int(8 * u) - int(1.5 * u), y0, 3 * u, sh, lit)

    for r, half in enumerate([4, 5, 5, 5, 4, 3]):
        y = y0 + (4 + r) * u
        rect(pen, cx - half * u, y, 2 * half * u, u, gold if r == 1 else metal)
        rect(pen, cx - half * u, y, u, u, lit)
        rect(pen, cx + (half - 1) * u, y, u, u, dark)

    rect(pen, cx, y0 + 5 * u, 3 * u, 3 * u, "#14100e")

    for k in range(5):
        rect(pen, cx + (3 + k) * u, y0 + (4 - k) * u, u, u, "#2b2624")
        rect(pen, cx + (3 + k) * u, y0 + (5 - k) * u - 2, u, 2, "#7a746c")

    rect(pen, cx - 3 * u, y0 + 10 * u, max(2, u // 2), 5 * u, lit)
    rect(pen, cx - 5 * u, y0 + 15 * u, 5 * u, sh, lit)
    rect(pen, cx - 4 * u, y0 + 15 * u - sh, 3 * u, sh, metal)
    rect(pen, cx + 2 * u, y0 + 10 * u - sh, u, sh, "#5a1212")


# ============================================================
# the walking scene


def draw_walk(st):
    pal, pan, tv = PAL[st["pal"]], st["pan"], st["travel"]
    sv = st.get("scenery", tv)
    fwd = st.get("dir", 0)
    s0 = pal["seed"]

    bands(pal["sky"], 300, 13, 20)

    sc = scol(SUN_COL, pan, 10)
    if sc is not None:
        cx, cy = X(sc), HORIZON + pal["sun_h"]
        disc(cx, cy, 8, pal["halo"], HORIZON)
        disc(cx, cy, 5, pal["glow"], HORIZON)
        disc(cx, cy, 3, pal["sun"], HORIZON)

    # each layer uses a different zoom rate. the closer it is, the faster
    # it grows as we walk, which creates the parallax effect.
    xs = sample(pan, zoom_for(0.03, sv, pan, fwd))
    mesa = [HORIZON + (q(8 + terrain(x, 23 + s0, 90) * 22)
                       if terrain(x, 29 + s0, 30) > 0.52 else 0) for x in xs]
    layer(mesa, pal["mesa_l"], pal["mesa"], P, HORIZON)

    xs = sample(pan, zoom_for(0.07, sv, pan, fwd))
    dome = [HORIZON + q(6 + terrain(x, 11 + s0, 40) * (34 + 3 * sv)) for x in xs]
    layer(dome, pal["far_l"], pal["far"], P, HORIZON)

    xs = sample(pan, zoom_for(0.16, sv, pan, fwd))
    near = [HORIZON + q(terrain(x, 47 + s0, 10) * (12 + 2 * sv)) for x in xs]
    layer(near, pal["near_l"], pal["near"], 0, HORIZON)

    rise = st["rise"] if st.get("rise") is not None else lerp_list(RISE, sv)

    if rise > 1:
        xs = sample(pan, zoom_for(0.10, sv, pan, fwd))
        tops = []

        for x in xs:
            t = max(0.0, 1 - abs(heading(x)) / SLOPE_HALF)

            # the height fades towards the sides, leaving the main rise
            # in front of us instead of stretching across the whole horizon.
            tops.append(HORIZON + q(rise * t * t * (3 - 2 * t)
                                    * (0.9 + 0.2 * terrain(x, 61 + s0, 5))))

        layer(tops, pal["slope_l"], pal["slope"], P, HORIZON)
        contours(tops, range(20, 110, 20), pal["strata"], HORIZON)

    bands(pal["ground"], HORIZON, 17, 20)
    draw_ripples(pal, pan, tv, s0, HORIZON, DEPTH_PER_STEP)

    lsc = scol(LANDER_COL, pan, 20) if st.get("lander", True) else None
    draw_rocks(pal, pan, tv, s0, HORIZON, DEPTH_PER_STEP, avoid=lsc)

    if lsc is not None:
        draw_lander(pal, lsc, min(len(LANDER_U) - 1, int(round(tv))))


# ============================================================
# the canyon vista


def draw_canyon():
    cv, pts = CANYON, CANYON_PTS
    bands(cv["sky"], 300, 12, 20)

    for r, c in cv["sun"]:
        disc(X(69), 178, r, c, V_HORIZON)

    bands(cv["basin"], V_HORIZON, 14, 20)

    # scatter some small ripples across the basin, with a few larger dunes
    # closer to the viewer.
    for i in range(30):
        d = rnd(i * 5 + 1) ** 1.3
        w = int((3 + rnd(i * 5 + 3) * 6) * P * (1 + d * 2))
        rect(pen, X(int(rnd(i * 5 + 2) * COLS)), q(V_HORIZON - 8 - d * 250), w,
             3 + int(d * 4), "#ecd2b6" if i % 2 else "#b48a6e")

    for col, y, w in ((20, 24, 150), (50, -8, 210), (14, -66, 260)):
        x = X(col)
        rect(pen, x, y, w, 3, "#f0d8bc")
        rect(pen, x + 8, y - 4, w - 20, 4, "#b98f74")
        rect(pen, x + 24, y - 8, max(8, w - 56), 4, "#c9a088")

    layer(ridge(pts["mesa"], seed=5, jag=4, run=(3, 6)),
          cv["mesa"][0], cv["mesa"][1], P, V_HORIZON)

    # the three ridgelines use different seeds and jaggedness so they don't
    # end up looking like copies of the same mountain.
    massif = ridge(pts["massif"], seed=3, jag=16)
    cliff_face(massif, 52, cv["massif"], seed=7, gullies=9, haze_h=56)

    wall = ridge(pts["wall"], seed=13, jag=18)
    cliff_face(wall, -300, cv["wall"], seed=21, gullies=6)

    outcrop = ridge(pts["outcrop"], seed=29, jag=14)
    cliff_face(outcrop, -300, cv["outcrop"], seed=33, gullies=5)

    if CANYON_RUBBLE:
        for i in range(9):
            c = int(rnd(i * 7 + 1) * 40)
            if outcrop[c] > -150:
                chunk(X(c) - 8, outcrop[c] - 4, 36 + int(rnd(i * 7 + 2) * 44),
                      24 + int(rnd(i * 7 + 3) * 28), cv["rubble"], seed=i)

        for i in range(6):
            c = 49 + int(rnd(i * 11 + 3) * 46)
            if wall[c] > -120:
                chunk(X(c) - 8, wall[c] - 4, 28 + int(rnd(i * 11 + 4) * 30),
                      18 + int(rnd(i * 11 + 5) * 22), cv["rubble"], seed=40 + i)

    puff(X(8), 36, 56)
    puff(X(38), 4, 44, "#e0bc9e", "#ecd2b6")
    puff(X(84), 66, 70)

    rect(pen, -400, -254, 800, 64, "#0a0303")
    rect(pen, -400, -192, 800, 2, DIM)


# ============================================================
# scenes


class Boot(Scene):
    hud = False

    def enter(self, game):
        game.busy = True
        type_lines(BOOT, -370, 200, FONT, OCHRE,
                   lambda: game.after(1600, lambda: game.go("walk")))


class Walk(Scene):
    def enter(self, game):
        txt.clear()
        game.set_storm(True)
        game.busy = False
        game.render()

    def draw(self, game):
        draw_walk(game.state)

    def hud_info(self, game):
        st = game.state
        hint = None

        if not game.busy:
            hint = "[ CLICK TO ADVANCE ]" if st["look"] == 0 else "[ CLICK TO FACE FORWARD ]"

        return dict(top=top_bar(st), msg=st["msg"], hint=hint)

    def storm(self, game):
        st = game.state
        return dict(key="walk", colors=PAL[st["pal"]]["grain"], ymin=-250, ymax=262,
                    ycenter=-30, yspread=130, streaks=7,
                    level=lambda g: min(1.0, 0.22 + 0.09 * st["travel"] + 0.30 * g))

    # ---- input

    def on_click(self, game, x, y):
        st = game.state

        if st["look"] != 0:
            st["look"] = 0
            st["pan"] = FORWARD_PAN

        self.advance(game)

    def on_key(self, game, key):
        st = game.state

        if st["steps"] < RIDGE_AT:
            self.sweep(game, 180 if st["look"] == 0 else 0)

    # ---- the walk

    def advance(self, game):
        st = game.state
        n = st["steps"] + 1
        st["steps"] = n
        game.busy = True

        a_tv, a_odo, a_clk = st["travel"], st["odo"], st["clock_min"]
        b_odo, b_clk = a_odo + LEG_METERS[n], minutes(CLOCKS[n])
        st["msg"] = WALK_MSG

        def frame(p, elapsed):
            e = ease(p)
            st["travel"] = lerp(a_tv, n, e)
            st["odo"] = lerp(a_odo, b_odo, e)
            st["clock_min"] = lerp(a_clk, b_clk, e)

            # alternate the camera dip every half-stride, then reset it
            # when the walking animation finishes.
            view["dy"] = -BOB_PX if (p < 1 and int(elapsed / (STRIDE_SECONDS / 2)) % 2) else 0

            game.render()

        tween(WALK_SECONDS, frame, lambda: self.arrive(game, n))

    def arrive(self, game, n):
        game.state["msg"] = FORWARD_MSGS[n]

        if n == RIDGE_AT:
            game.render()
            game.after(1200, lambda: self.to_canyon(game))
            return

        game.busy = n == JUMP_AT
        game.render()

        if n == JUMP_AT:
            game.after(1500, lambda: self.timelapse(game))

    def sweep(self, game, target):
        st = game.state
        game.busy = True
        st["look"] = target

        start = st["pan"]
        goal = (target - COLS // 2) % WORLD

        # find the shortest way around the circular world instead of
        # making the camera rotate almost a full 360 degrees.
        delta = ((goal - start + 180) % WORLD) - 180

        st["msg"] = TURNING_MSG

        def tick(i=1):
            st["pan"] = int(round(start + delta * i / PAN_FRAMES)) % WORLD
            last = i == PAN_FRAMES

            if last:
                lost = not st.get("lander", True)
                st["msg"] = (NO_LANDER_MSG if lost else LOOK_BACK_MSG) if target else FACE_FORWARD_MSG
                game.busy = False

            game.render()

            if not last:
                game.after(60, lambda: tick(i + 1))

        tick()

    # ---- story beats

    def timelapse(self, game):
        big = ("Courier", 24, "bold")
        game.set_storm(False)

        def resume():
            fx.clear()
            txt.clear()

            game.state.update(pal="afternoon", clock_min=minutes(POST_JUMP_CLOCK),
                              msg=AFTER_JUMP_MSG, lander=False)

            game.set_storm(True)
            game.busy = False
            game.render()

        def hold():
            game.after(1800, lambda: fade_text([TIMELAPSE_TEXT], 10, big, OCHRE, resume, True))

        wipe(lambda: fade_text([TIMELAPSE_TEXT], 10, big, OCHRE, hold))

    def to_canyon(self, game):
        game.set_storm(False)
        wipe(lambda: game.after(700, lambda: game.go("canyon")))


class Canyon(Scene):
    def __init__(self, then=None):
        self.then = then

    def enter(self, game):
        fx.clear()
        txt.clear()
        game.state["msg"] = VISTA_MSG
        game.busy = True
        game.set_storm(True)
        game.render()
        game.after(3500, lambda: self.final_lines(game))

    def draw(self, game):
        draw_canyon()

    def hud_info(self, game):
        st = game.state
        hint = TURN_BACK_HINT if (self.then and not game.busy) else None
        return dict(top=top_bar(st), msg=st["msg"], hint=hint)

    def on_click(self, game, x, y):
        self.turn_back(game)

    def on_key(self, game, key):
        self.turn_back(game)

    def turn_back(self, game):
        game.busy = True
        game.state["msg"] = TURN_BACK_MSG
        game.refresh_hud()
        game.set_storm(False)
        wipe(lambda: game.after(600, lambda: self.then(game)))

    def storm(self, game):
        # keep the particles above the caption strip so they don't cover the text.
        return dict(key="canyon", colors=CANYON["grain"], ymin=-184, ymax=262,
                    ycenter=70, yspread=110, streaks=16, count=260,
                    level=lambda g: min(1.0, 0.70 + 0.30 * g))

    def final_lines(self, game):
        fade_text(FINAL_LINES, -212, ("Courier", 14, "bold"), OCHRE,
                  lambda: self.await_turn(game))

    def await_turn(self, game):
        if self.then:
            game.busy = False
            game.refresh_hud()
        else:
            game.after(5000, lambda: self.end_card(game))

    def end_card(self, game):
        game.set_storm(False)

        def show():
            txt.clear()
            fade_text([END_CARD], 0, FONT, DIM)

        wipe(show)


# ============================================================
# hook-up


def install(game, then=None):
    game.state.update(steps=0, travel=0.0, odo=0.0, clock_min=minutes(CLOCKS[0]),
                      pan=FORWARD_PAN, look=0, pal="morning",
                      msg="System: Link established.")

    game.add("boot", Boot())
    game.add("walk", Walk())
    game.add("canyon", Canyon(then))
    return "boot"