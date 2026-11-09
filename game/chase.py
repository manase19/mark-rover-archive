"""
    cliff    you are facing away ;-; click to turn back
    turn     the view swings around to face the plain
    seen     the entity stands on the plain, the radiation alarm is going
    run      click to run. clicks queue up and the run is smooth. B / Down looks
             behind: the entity is drawn at its current distance, in discrete
             levels (state["gap"]). It closes one level every CATCH_EVERY strides
             and every IDLE_SECONDS you stand, so you cant outrun it
    dead     caught: the screen tears and flickers, then SIGNAL LOST

hooked up from main.py with  opening.install(game, then=chase.begin).
"""
import time
import os
import sys
import subprocess

from art import X, scol
from config import (BOB_PX, CATCH_EVERY, CAUGHT_MSG, CLIFF_HINT, CLIFF_MSG, COLS,
                    FLICKER_SECONDS, FONT,
                    FORWARD_PAN, GAP_MAX, HORIZON, IDLE_SECONDS, LOST_LINES, MAX_QUEUE,
                    METERS_PER_GAP, METERS_PER_STRIDE, MONSTER_U, OCHRE, PAL, RAD_BASE,
                    RAD_NORMAL, RAD_STEP, RUN_HINT, RUN_MSG, RUN_MSG_CRITICAL,
                    RUN_SPEED, SIGHTING_MSG, SIGHTING_MSG2, SOURCE_MSG, TITLE,
                    TURN_RIGHT_HINT, TURN_RIGHT_MSG, W, WORLD, NO_SIGNAL_FRAME_MS, NO_SIGNAL_TEXT,)
from engine import (Scene, clock_text, fx, mix, pen, q, rect, rnd, screen,
                    tween, txt, type_lines, view)
from opening import draw_walk

TURN_BACK_MSG = "You turn around."


# ============================================================ look
def make_dusk(pal):
    """A darker, redder copy of a palette (the sun is almost gone)."""
    def dim(v):
        if isinstance(v, str):
            return mix(v, "#10050a", 0.55)
        if isinstance(v, (list, tuple)):
            return type(v)(dim(x) for x in v)
        return v
    out = {k: dim(v) for k, v in pal.items()}
    out.update(seed=1000, sun_h=6, sun="#d85a30", glow="#9a2a1a", halo="#5a1a14")
    return out


BODY, RIM, HALO, EYE = "#030101", "#2a100d", "#5a0a0a", "#ff2020"
# Entity parts as (x0, x1, y0, y1) in units of its pixel size u, x from its centre line.
PARTS = [(-1.5, -0.5, 0, 8), (0.5, 1.5, 0, 8),        # legs
         (-1.5, 1.5, 8, 15),                           # torso
         (-3.0, 3.0, 14, 15),                          # shoulders
         (-3.5, -2.5, 3, 15), (2.5, 3.5, 3, 15),       # arms hanging to the knees
         (-0.5, 0.5, 15, 16),                          # neck
         (-1.5, 1.5, 16, 20)]                          # head
EYES = [(-1.1, -0.3), (0.3, 1.1)]


def draw_monster(gap, cx, tick):
    """tall black figure (who is the pilot) with two red eyes, centred at screen x = cx. Its size and
    ground position come from `gap`, so each level is a visible jump closer."""
    u = MONSTER_U[gap]
    d = 1 - gap / float(GAP_MAX)
    y0 = q(HORIZON - 8 - (d ** 1.5) * 250)
    cx += u if (tick // 6) % 9 == 0 else 0                 # an occasional twitch to the side
    r = max(1, u // 5)

    def part(a, b, c, e, col, grow=0):
        rect(pen, cx + a * u - grow, y0 + c * u - grow, (b - a) * u + 2 * grow, (e - c) * u + 2 * grow, col)

    for p in PARTS:
        part(p[0], p[1], p[2], p[3], RIM, r)               # faint rim so it reads against dark ground
    for p in PARTS:
        part(p[0], p[1], p[2], p[3], BODY)
    if (tick // 5) % 17:                                   # eyes, with the odd blink
        for a, b in EYES:
            part(a, b, 18, 19, HALO, max(1, u * 0.5))
            part(a, b, 18, 19, EYE)


# ============================================================ HUD
def top_bar(st):
    rad = RAD_NORMAL if not st["monster"] else RAD_BASE + (GAP_MAX - st["gap"]) * RAD_STEP
    return [(-388, "left", TITLE),
            (-100, "center", "RAD %04d" % rad),
            (0, "center", "HDG %03d" % ((st["pan"] + COLS // 2 + 180) % WORLD)),
            (225, "right", "ODOM %04d m" % st["odo"]),
            (388, "right", "SOL 0001  " + clock_text(st["clock_min"]))]


# ============================================================ the scene
class Chase(Scene):
    def __init__(self):
        self.running = False
        self.t_last = 0.0

    # ---- plumbing
    def enter(self, game):
        game.set_storm(True)
        game.busy = False
        game.render()
        self.idle_loop(game)

    def draw(self, game):
        st = game.state
        draw_walk(st)
        sc = scol(st["mcol"], st["pan"], 20)
        visible = (st["phase"] == "seen" and st["look"] == 0) or \
                  (st["phase"] in ("run", "dead") and st["look"] != 0)
        if st["monster"] and visible and sc is not None and sc > -12:
            draw_monster(st["gap"], X(sc), st["tick"])

    def hud_info(self, game):
        st = game.state
        hint = None
        if not game.busy:
            hint = {"cliff": CLIFF_HINT, "seen": TURN_RIGHT_HINT}.get(st["phase"])
            if st["phase"] == "run":
                hint = RUN_HINT if st["look"] == 0 else "[ CLICK TO FACE FORWARD ]"
        return dict(top=top_bar(st), msg=st["msg"], hint=hint)

    def storm(self, game):
        st = game.state
        return dict(key="chase", colors=PAL["dusk"]["grain"], ymin=-250, ymax=262,
                    ycenter=-30, yspread=130, streaks=9,
                    level=lambda g: min(1.0, 0.35 + 0.012 * st["strides"] + 0.30 * g))

    def pan_for(self, st, back):
        return (st["dir"] + (180 if back else 0) - COLS // 2) % WORLD

    def turn_to(self, game, goal, frames, done):
        """Pan the view to heading-pan `goal` in a few frames, then call done()."""
        st = game.state
        game.busy = True
        start = st["pan"]
        delta = ((goal - start + 180) % WORLD) - 180

        def tick(i=1):
            st["pan"] = int(round(start + delta * i / frames)) % WORLD
            game.render()
            if i < frames:
                game.after(60, lambda: tick(i + 1))
            else:
                done()
        tick()

    # ---- input
    def on_click(self, game, x, y):
        st = game.state
        phase = st["phase"]
        if phase == "cliff":
            self.turn_back(game)
        elif phase == "seen":
            self.turn_right(game)
        elif phase == "run":
            if st["look"] != 0:                              # a click snaps the view forward
                st["look"] = 0
                st["pan"] = self.pan_for(st, False)
                st["msg"] = RUN_MSG
            st["last_input"] = time.monotonic()
            st["target"] = min(st["target"] + 1, st["travel"] + MAX_QUEUE)
            self.start_run(game)

    def on_key(self, game, key):
        st = game.state
        if st["phase"] != "run":
            return
        back = st["look"] == 0
        st["look"] = 180 if back else 0

        def done():
            st["msg"] = self.look_msg(st) if back else RUN_MSG
            game.busy = False
            game.render()
        self.turn_to(game, self.pan_for(st, back), 4, done)

    def look_msg(self, st):
        return SOURCE_MSG % (st["gap"] * METERS_PER_GAP)

    # ---- phase 1: turn back, see it
    def turn_back(self, game):
        st = game.state
        st["phase"] = "turn"
        st["msg"] = TURN_BACK_MSG
        self.turn_to(game, FORWARD_PAN, 6, lambda: self.sighting(game))

    def sighting(self, game):
        st = game.state
        st.update(phase="seen", monster=True, gap=GAP_MAX, mcol=0, msg=SIGHTING_MSG)
        game.busy = False
        game.render()
        game.after(2800, lambda: self.second_warning(game))

    def second_warning(self, game):
        st = game.state
        if st["phase"] == "seen":
            st["msg"] = SIGHTING_MSG2
            game.render()

    # ---- phase 2: turn right and run
    def turn_right(self, game):
        st = game.state
        st["msg"] = TURN_RIGHT_MSG
        goal = (FORWARD_PAN + 90) % WORLD

        def done():
            st.update(dir=90, mcol=270, phase="run", msg=RUN_MSG, strides=0,
                      t0=st["travel"], target=st["travel"], last_input=time.monotonic())
            game.busy = False
            game.render()
        self.turn_to(game, goal, 6, done)

    def start_run(self, game):
        if not self.running:
            self.running = True
            self.t_last = time.monotonic()
            self.run_frame(game)

    def run_frame(self, game):
        """advance toward the queued target at RUN_SPEED, redrawing as we go."""
        st = game.state
        now = time.monotonic()
        dt, self.t_last = now - self.t_last, now
        if st["phase"] != "run" or st["look"] != 0 or st["travel"] >= st["target"]:
            self.running = False                             # nothing queued (or looking back)
            view["dy"] = 0
            if st["phase"] == "run":
                game.render()
            return
        step = RUN_SPEED * dt
        st["travel"] = min(st["target"], st["travel"] + step)
        st["odo"] += step * METERS_PER_STRIDE
        st["clock_min"] += step * 0.4
        view["dy"] = -BOB_PX if int(now * RUN_SPEED * 2) % 2 else 0
        n = int(st["travel"] - st["t0"])
        if n > st["strides"]:
            st["strides"] = n
            if n % CATCH_EVERY == 0:
                self.close_in(game)
        if st["phase"] == "run":
            game.render()
            game.after(1, lambda: self.run_frame(game))
        else:
            self.running = False

    def idle_loop(self, game):
        """standing still lets it catch up: one level per IDLE_SECONDS."""
        st = game.state
        if st["phase"] == "dead":
            return
        if st["phase"] == "run" and time.monotonic() - st["last_input"] > IDLE_SECONDS:
            st["last_input"] = time.monotonic()
            self.close_in(game)
        game.after(500, lambda: self.idle_loop(game))

    def close_in(self, game):
        """the entity gains one discrete level. At level 0 it has you."""
        st = game.state
        st["gap"] = max(0, st["gap"] - 1)
        if st["gap"] == 0:
            self.caught(game)
            return
        if st["look"] != 0:
            st["msg"] = self.look_msg(st)
        else:
            st["msg"] = RUN_MSG_CRITICAL if st["gap"] <= 2 else RUN_MSG
        if not self.running:
            game.render()                                    # (a running loop redraws anyway)

    # ---- phase 3: caught
    def caught(self, game):
        st = game.state
        st.update(phase="dead", gap=0, look=180, msg=CAUGHT_MSG)
        st["pan"] = self.pan_for(st, True)
        game.busy = True
        view["dy"] = 0
        game.render()
        game.after(900, lambda: self.flicker(game))

    def flicker(self, game):
        """tear and strobe the screen, black frames getting likelier, then cut to black."""
        game.set_storm(False)

        def frame(p, elapsed):
            fx.clear()
            k = int(elapsed * 30)                            # a new pattern ~30 times a second
            r = rnd(k * 7 + 3)
            if r < 0.20 + 0.70 * p:
                rect(fx, -400, -300, W, 600, "black")
            elif r < 0.27:
                rect(fx, -400, -300, W, 600, "#3a0000")
            else:
                for i in range(3 + int(8 * rnd(k))):         # horizontal tearing and static
                    y = int(rnd(k * 13 + i) * 560) - 280
                    h = 4 + int(rnd(k * 17 + i) * 28)
                    x = int(rnd(k * 19 + i) * 300) - 400
                    w = 300 + int(rnd(k * 29 + i) * 500)
                    rect(fx, x, y, w, h, "black" if rnd(k * 23 + i) < 0.55 else OCHRE)
            screen.update()
        tween(FLICKER_SECONDS, frame, lambda: self.signal_lost(game))

    def no_signal(self, game):
        """Display NO SIGNAL, close the window, and launch prologue.py."""
        k = [0]
        start_time = time.monotonic()

        project_dir = os.path.dirname(os.path.abspath(__file__))
        prologue_path = os.path.join(project_dir, "prologue.py")

        def launch_prologue():
            if getattr(sys, "frozen", False):
                # running inside the packaged EXE.
                command = [sys.executable, "--prologue"]
                env = os.environ.copy()

                env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

                cwd = os.path.dirname(sys.executable)

            else:
                # Running directly from Python.
                project_dir = os.path.dirname(
                    os.path.abspath(__file__)
                )

                command = [
                    sys.executable,
                    os.path.join(project_dir, "prologue.py")
                ]

                env = None
                cwd = project_dir

            screen.bye()

            subprocess.Popen(
                command,
                cwd=cwd,
                env=env
            )

        def frame():
            # display the NO SIGNAL screen for 6 seconds.
            if time.monotonic() - start_time >= 6:
                launch_prologue()
                return

            draw_no_signal(k[0])
            k[0] += 1

            screen.update()
            game.after(NO_SIGNAL_FRAME_MS, frame)

        frame()

    def signal_lost(self, game):
        fx.clear()
        rect(fx, -400, -300, W, 600, "black")
        txt.clear()
        screen.update()

        def end():
            txt.clear()
            self.no_signal(game)

        type_lines(LOST_LINES, -370, 80, FONT, OCHRE, lambda: game.after(3500, end))


# ============================================================ the dead channel
# test card rows as (colour, x0, x1) with x as a fraction of the screen width.
def _row(colors, cuts):
    return [(c, cuts[i], cuts[i + 1]) for i, c in enumerate(colors)]

_SEVEN = [i / 7.0 for i in range(8)]
CARD = [(300, 408, _row(["#c0c0c0", "#e8e810", "#10e8e8", "#10e810", "#e810e8", "#e81010",
                         "#1010e8"], _SEVEN)),
        (-108, 90, _row(["#1010e8", "#000000", "#e8e810", "#000000", "#10e8e8", "#000000",
                         "#c0c0c0"], _SEVEN)),
        (-198, 102, _row(["#1010a8", "#ffffff", "#1010a8", "#000000", "#808080", "#000000"],
                         [0, .19, .37, .55, .81, .85, 1.0]))]

def draw_no_signal(k):
    """frame k of a failing TV: colour bars and a NO SIGNAL box that tear sideways,
    dim, drop out and go black at random. Drawn on the fx pen only, so it is cheap."""
    fx.clear()
    r = rnd(k * 5 + 1)
    if r < 0.10:                                            # signal drops: black frame
        rect(fx, -400, -300, W, 600, "black")
        return
    dim = r < 0.30                                          # brightness sags
    def c(col):
        return mix(col, "#000000", 0.45) if dim else col
    for n, (y, h, segs) in enumerate(CARD):
        dx = int((rnd(k * 7 + n) - 0.5) * 160) if rnd(k * 11 + n) < 0.25 else 0   # row tears
        for col, a, b in segs:
            rect(fx, -400 + a * W + dx, y, (b - a) * W, h, c(col))
        if dx > 0:
            rect(fx, -400, y, dx, h, "black")
        elif dx < 0:
            rect(fx, 400 + dx, y, -dx, h, "black")
    for i in range(int(rnd(k * 3) * 4)):                    # static lines
        rect(fx, int(rnd(k * 13 + i) * 400) - 400, int(rnd(k * 17 + i) * 560) - 280,
             200 + int(rnd(k * 19 + i) * 600), 3 + int(rnd(k * 23 + i) * 8),
             "#ffffff" if rnd(k * 29 + i) < 0.5 else "#808080")
    rect(fx, -256, -112, 512, 217, c("#1c1c1c"))
    if rnd(k * 9 + 2) > 0.08:                               # the label sometimes drops out
        fx.color(c("#ffffff"))
        fx.goto(int((rnd(k * 31) - 0.5) * 24), -30)
        fx.write(NO_SIGNAL_TEXT, align="center", font=("Courier", 30, "bold"))


# ============================================================ hook-up
def begin(game):
    """Start chapter 2 (called by opening.install(..., then=chase.begin))."""
    PAL["dusk"] = make_dusk(PAL["afternoon"])
    game.state.update(pal="dusk", travel=0.0, scenery=2.0, rise=0, lander=False,
                      pan=(FORWARD_PAN + 180) % WORLD, look=0, dir=0, phase="cliff",
                      monster=False, gap=GAP_MAX, mcol=0, strides=0, t0=0.0,
                      target=0.0, last_input=0.0, msg=CLIFF_MSG)
    game.add("chase", Chase())
    game.go("chase")