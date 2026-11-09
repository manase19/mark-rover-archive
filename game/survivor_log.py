# survivor_log.py : Scene 1 of the survivor's video log.
# run the full sequence with: python main.py
# runtime dependendencies: Python standard library only (turtle + time).
# keep habitat.gif and pilot.gif in the ./assets/ folder.

import turtle
import time
from pathlib import Path

W, H = 900, 600
HUD = "#cfd6dc"
GREYS = ("#e8ecef", "#9aa1aa", "#5b616b", "#2a2e35", "#c9ced4")
ASSET_DIR = Path(__file__).resolve().parent / "assets"
START_MINUTES = 11 * 60 + 19

LINES = [
    "Oh man!! I still can't believe the rocket failed!!\n"
    "Forty-two seconds into yesterday's static fire, the\n"
    "turbopump seal gave out and the engine just quit.",

    "For the record: November tenth, 1988.\n"
    "We have just landed 25 hours ago,\n"
    "That is, we are already on Mars.",

    "Everybody here is really stressed. The Captain has\n"
    "run the numbers four times. Same answer: It's burnt.",

    "But we're pretty optimistic.\n"
    "He said NASA's engineers would have expected this\n"
    "kind of return stage failure.",

    "Anyway, I'm sending this up on the next relay pass.\n"
    "So Houston, if you're watching: we're alive, we're\n"
    "fed, and we're not mad. Okay, we're a little mad.",

    "We can't turn back now!\n"
    "So we stay, we make this place last, and we wait\n"
    "for you to come get us.",
]

_seed = 2024


def rnd(limit):
    """Small deterministic generator; avoids importing random."""
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7fffffff
    return (_seed >> 8) % limit


def asset(filename):
    return str(ASSET_DIR / filename)


def pen(stamper=False):
    t = turtle.Turtle(visible=False)
    t.penup()
    t.speed(0)
    if stamper:
        t.shape("square")
    return t


def rect(t, x, y, w, h, color):
    t.penup()
    t.color(color)
    t.goto(x, y)
    t.pendown()
    t.begin_fill()
    for point in ((x + w, y), (x + w, y - h), (x, y - h), (x, y)):
        t.goto(point)
    t.end_fill()
    t.penup()


def text(t, x, y, value, size=12, color=HUD, align="left"):
    t.penup()
    t.goto(x, y)
    t.color(color)
    t.write(value, align=align, font=("Courier", size, "bold"))


def stamp_rect(t, x, y, w, h, color):
    """Stamp a stretched Turtle square; x/y are the top-left corner."""
    t.color(color)
    t.shapesize(h / 20, w / 20)
    t.goto(x + w / 2, y - h / 2)
    t.stamp()


def noise_frame():
    blocks = [
        (rnd(W) - W // 2, rnd(H) - H // 2,
         (1 + rnd(4)) * 6, (1 + rnd(2)) * 3,
         GREYS[rnd(len(GREYS))])
        for _ in range(42)
    ]
    blocks.append((-W // 2, rnd(H) - H // 2, W, 3, "#9aa1aa"))
    return blocks


def play(screen, on_done):
    """Play Scene 1 in the supplied Turtle window, then call on_done()."""
    screen.title("HAB TERMINAL")
    screen.bgcolor("#14171c")
    screen.tracer(0)

    # Register the two image assets from the shared assets folder.
    screen.addshape(asset("habitat.gif"))
    screen.addshape(asset("pilot.gif"))

    habitat = pen()
    habitat.shape(asset("habitat.gif"))
    habitat.goto(0, 0)
    habitat.stamp()

    pilot = pen()
    pilot.shape(asset("pilot.gif"))
    pilot.goto(0, 74)
    pilot.stamp()

    bg, ui, fx = pen(), pen(), pen(True)
    clock = pen()

    # ---- Static HUD ----
    bg.pensize(1)
    bg.color(HUD)
    for x, bottom, direction in ((-440, -285, 1), (440, -140, -1)):
        bg.goto(x, 285)
        bg.pendown()
        bg.goto(x, bottom)
        bg.penup()
        bg.goto(x, 0)
        bg.pendown()
        bg.goto(x + 12 * direction, 0)
        bg.penup()

    text(bg, -420, 272, "MISSION DAY", 12)
    rect(bg, -422, 262, 150, 34, "#6b7480")
    text(bg, -414, 232, "SOL 012", 18, "#e8edf1")

    for index, (label, value, unit) in enumerate((
        ("PRESSURE", "12.48", "PSI"),
        ("OXYGEN", "20.77", "%"),
        ("TEMP", "21.07", "C"),
    )):
        y = 188 - index * 70
        text(bg, -420, y, label, 11)
        text(bg, -420, y - 30, value, 16, "#e8edf1")
        bg.goto(-318, y - 14)
        bg.dot(42, HUD)
        bg.dot(34, "#171b22")
        text(bg, -318, y - 21, unit, 9, align="center")

    text(bg, -420, -22, "ENVIRONMENT", 11)
    text(bg, 424, 244, "LOG ENTRY > PILOT #01", 14, align="right")
    text(bg, 424, 216, "EARTH DATE 10 NOV 1988", 14, align="right")
    text(bg, -420, -250, "HAB TERMINAL", 16, "#e8edf1")
    text(bg, -420, -280, "CONNECTED:4002040-24-3", 8)

    # Dialogue panel is deliberately below the pilot's hands.
    rect(bg, -252, -153, 694, 144, HUD)
    rect(bg, -250, -155, 690, 140, "#10141a")
    text(bg, -236, -172, "PILOT", 10, "#7f8a96")

    # The clock has its own writer so the static HUD is not redrawn.
    def update_clock(entry_number):
        total = START_MINUTES + entry_number
        hours, minutes = divmod(total, 60)
        clock.clear()
        text(clock, 424, 272, "TIME %02d:%02d" % (hours, minutes),
             14, align="right")

    def show(message, entry_number):
        ui.clear()
        for row, content in enumerate(message.split("\n")):
            text(ui, -236, -200 - row * 24, content, 14, "#e8edf1")
        update_clock(entry_number)
        screen.update()

    # Static noise uses two reusable sets of Turtle square stamps.
    frames = (noise_frame(), noise_frame())
    glitch = {"burst": 0, "frame": 0, "next": time.monotonic() + 1.5}
    running = {"active": True}
    finished = {"value": False}

    def update_glitch():
        if not running["active"]:
            return

        now = time.monotonic()
        changed = False
        if glitch["burst"]:
            fx.clearstamps()
            for block in frames[glitch["frame"]]:
                stamp_rect(fx, *block)
            glitch["frame"] = 1 - glitch["frame"]
            glitch["burst"] -= 1
            changed = True
            if not glitch["burst"]:
                glitch["next"] = now + 1.0 + rnd(90) / 100
        elif now >= glitch["next"]:
            glitch["burst"] = 5 + rnd(5)
            changed = True

        if changed:
            screen.update()
        if running["active"]:
            screen.ontimer(update_glitch, 90)

    def finish():
        if finished["value"]:
            return
        finished["value"] = True
        running["active"] = False
        fx.clearstamps()
        ui.clear()
        clock.clear()
        text(ui, 0, -200, "[ END OF ENTRY ]", 14,
             "#e8edf1", align="center")
        screen.update()

        # Allow the end card to remain visible before main.py starts Scene 2.
        screen.ontimer(on_done, 1500)

    def start_entry(entry_number=0):
        if not running["active"]:
            return
        if entry_number >= len(LINES):
            finish()
            return

        entry = LINES[entry_number]
        index = 0

        def type_character():
            nonlocal index
            if not running["active"]:
                return
            index += 1
            show(entry[:index], entry_number)
            if index < len(entry):
                screen.ontimer(type_character, 30)
            else:
                pause = int((1.2 + len(entry) / 80) * 1000)
                screen.ontimer(lambda: start_entry(entry_number + 1), pause)

        type_character()

    show("", 0)
    screen.ontimer(update_glitch, 90)
    screen.ontimer(start_entry, 1500)


if __name__ == "__main__":
    standalone_screen = turtle.Screen()
    standalone_screen.setup(W, H)
    play(standalone_screen, standalone_screen.bye)
    standalone_screen.mainloop()