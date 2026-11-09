import turtle
import time
from pathlib import Path


W, H = 900, 600
HUD = "#cfd6dc"
GREYS = ("#e8ecef", "#9aa1aa", "#5b616b", "#2a2e35", "#c9ced4")
ASSET_DIR = Path(__file__).resolve().parent / "assets"


# each beat has a speaker, their dialogue, and the poses of the two characters.
# the first sprite is the one speaking and the second shows the reaction.
BEATS = [
    ("CAPTAIN", "The rover is four kilometres from the lander.\nWe leave as soon as the suit checks are complete.", ("captain_talking", "specialist_side_look")),
    ("PILOT", "Captain, have we heard anything about the return stage?\nCan it still fire?", ("pilot_thinking", "captain_looking")),
    ("CAPTAIN", "We haven't had a full assessment yet. Houston has the\nflight data. Until they tell us otherwise, we follow the plan.", ("captain_talking", "pilot_listening")),
    ("PILOT", "And if the damage is worse than they think?\nWhat if there's no way to get us off this planet?", ("pilot_talking", "specialist_concerned")),
    ("CAPTAIN", "Then we'll deal with it when we know. We're not\nstranded yet. Right now, we have a rover to recover.", ("captain_arms_crossed", "pilot_listening")),
    ("PILOT", "Right. The rover.", ("pilot_thinking", "captain_looking")),
    ("SPECIALIST", "The four titanium tubes should still be inside.\nA-01 through A-04, if the latch hasn't failed.", ("specialist_talking", "captain_looking")),
    ("PILOT", "And the tapes? The U-matic reels?", ("pilot_talking", "specialist_side_look")),
    ("SPECIALIST", "If they survived, they're the only record\nof what MARK ROVER III found in that mudstone.", ("specialist_explaining", "pilot_listening")),
    ("CAPTAIN", "We'll recover the samples first. The reels\ncome second. We don't have room for mistakes.", ("captain_arms_crossed", "specialist_concerned")),
    ("PILOT", "Then why am I staying behind?", ("pilot_talking", "captain_looking")),
    ("CAPTAIN", "The relay needs an operator. If we miss the\nwindow, Houston won't hear from any of us.", ("captain_talking", "pilot_listening")),
    ("SPECIALIST", "And someone needs to watch the biomedical case.\nIts temperature seal is still holding.", ("specialist_explaining", "pilot_listening")),
    ("PILOT", "That's the case Houston refused to brief us on?", ("pilot_talking", "specialist_concerned")),
    ("SPECIALIST", "It's an adaptive compound. It was designed\nto help biological systems tolerate Mars conditions.", ("specialist_explaining", "pilot_listening")),
    ("PILOT", "Designed for the animals?", ("pilot_thinking", "specialist_side_look")),
    ("SPECIALIST", "The cat and the mouse were meant to be first.\nThe trials were never completed.", ("specialist_concerned", "pilot_listening")),
    ("CAPTAIN", "Houston has not authorised a human trial.\nThat is all we need to know about it.", ("captain_talking", "specialist_concerned")),
    ("PILOT", "How much did they send?", ("pilot_thinking", "captain_looking")),
    ("SPECIALIST", "Enough material for one theoretical\nhuman-equivalent dose. Not a proven dose.", ("specialist_explaining", "pilot_listening")),
    ("CAPTAIN", "Case stays sealed. Nobody experiments with it.\nWe are here to recover the rover, understood?", ("captain_arms_crossed", "pilot_listening")),
    ("PILOT", "Understood. I'll keep the relay open.", ("pilot_report", "captain_looking")),
    ("SPECIALIST", "We'll be back before the next relay window.", ("specialist_talking", "captain_looking")),
]


SPRITES = {
    "pilot": "pilot.gif",
    "pilot_talking": "pilot_talking_small.gif",
    "pilot_listening": "pilot_listening_small.gif",
    "pilot_report": "pilot_report_small.gif",
    "pilot_thinking": "pilot_thinking.gif",
    "pilot_reminiscing": "pilot_reminiscing.gif",
    "specialist": "specialist.gif",
    "specialist_talking": "specialist_talking_small.gif",
    "specialist_explaining": "specialist_explaining_small.gif",
    "specialist_concerned": "specialist_concerned.gif",
    "specialist_side_look": "specialist_side_look.gif",
    "specialist_report": "specialist_report.gif",
    "captain": "captain.gif",
    "captain_talking": "captain_talking.gif",
    "captain_looking": "captain_looking.gif",
    "captain_concerned": "captain_concerned.gif",
    "captain_arms_crossed": "captain_arms_crossed.gif",
}


def rnd(limit):
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7fffffff
    return (_seed >> 8) % limit


_seed = 2024


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
    t.color(color)
    t.shapesize(h / 20, w / 20)
    t.goto(x + w / 2, y - h / 2)
    t.stamp()


def noise_frame():
    blocks = [
        (rnd(W) - W // 2, rnd(H) - H // 2,
         (1 + rnd(4)) * 6, (1 + rnd(2)) * 3,
         GREYS[rnd(len(GREYS))])
        for _ in range(34)
    ]

    blocks.append((-W // 2, rnd(H) - H // 2, W, 3, "#9aa1aa"))
    return blocks


def draw_case(t, opened=False, vial=True):
    t.clear()
    x, y = 260, 105

    rect(t, x, y, 145, 78, "#8994a2")
    rect(t, x + 5, y - 5, 135, 68, "#28313e")
    rect(t, x + 12, y - 13, 121, 22, "#596575")

    if opened:
        rect(t, x + 5, y + 14, 135, 35, "#8994a2")
        rect(t, x + 10, y + 9, 125, 25, "#303b4a")
        rect(t, x + 16, y + 4, 113, 15, "#151c27")
        rect(t, x + 66, y - 35, 22, 20, "#0e141d")

        if vial:
            rect(t, x + 73, y - 36, 8, 5, "#d5a15b")
            rect(t, x + 74, y - 41, 6, 22, "#c5dce0")
            rect(t, x + 75, y - 50, 4, 9, "#8fb6ba")
            text(t, x + 96, y - 36, "1 DOSE", 7, "#e3e8eb")
        else:
            text(t, x + 96, y - 36, "REMOVED", 7, "#d36b60")

    else:
        rect(t, x + 18, y - 40, 108, 25, "#1b2430")
        rect(t, x + 61, y - 34, 22, 12, "#aeb8c4")
        text(t, x + 18, y - 30, "BIOMED / RESTRICTED", 7, "#d5dce3")
        text(t, x + 25, y - 60, "SEAL INTACT", 7, "#9eabb8")


def play(screen, on_done):
    screen.title("HAB TERMINAL — LOG ENTRY 02")
    screen.bgcolor("#14171c")
    screen.tracer(0)

    required_assets = {"habitat.gif"}
    required_assets.update(SPRITES.values())

    for filename in sorted(required_assets):
        screen.addshape(asset(filename))

    bg, cast_pen, panel_pen, ui, fx, case_pen, clock = (
        pen(), pen(), pen(), pen(), pen(True), pen(), pen()
    )

    habitat = pen()
    habitat.shape(asset("habitat.gif"))
    habitat.goto(0, 0)
    habitat.stamp()

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
    text(bg, -414, 232, "SOL 014", 18, "#e8edf1")

    for index, (label, value, unit) in enumerate((
        ("PRESSURE", "12.41", "PSI"),
        ("OXYGEN", "20.65", "%"),
        ("TEMP", "21.02", "C"),
    )):
        y = 188 - index * 70
        text(bg, -420, y, label, 11)
        text(bg, -420, y - 30, value, 16, "#e8edf1")
        bg.goto(-318, y - 14)
        bg.dot(42, HUD)
        bg.dot(34, "#171b22")
        text(bg, -318, y - 21, unit, 9, align="center")

    text(bg, -420, -22, "ENVIRONMENT", 11)
    text(bg, 424, 244, "LOG ENTRY > CREW #02", 14, align="right")
    text(bg, 424, 216, "EARTH DATE 12 NOV 1988", 14, align="right")
    text(bg, -420, -250, "HAB TERMINAL", 16, "#e8edf1")
    text(bg, -420, -280, "CONNECTED:4002040-24-3", 8)
    text(bg, 270, 110, "CLASSIFIED PAYLOAD", 8, "#d0d7df")
    draw_case(case_pen)

    def update_clock(beat_number):
        total = 15 * 60 + 27 + beat_number
        hours, minutes = divmod(total, 60)
        clock.clear()
        text(clock, 424, 272, "TIME %02d:%02d" % (hours, minutes), 14, align="right")

    def sprite_file(name):
        try:
            return asset(SPRITES[name])
        except KeyError:
            raise ValueError("Unknown sprite key: %s" % name)

    def draw_cast(names):
        cast_pen.clearstamps()
        cast_pen.clear()

        if len(names) == 1:
            cast_pen.shape(sprite_file(names[0]))
            cast_pen.goto(0, 72)
            cast_pen.stamp()

        else:
            # the sprites already have transparent space around the characters,
            # so these positions let both of them fit without cropping.
            positions = (-165, 155)

            for name, x in zip(names, positions):
                cast_pen.shape(sprite_file(name))
                cast_pen.goto(x + 60, 58)
                cast_pen.stamp()

    frames = (noise_frame(), noise_frame())
    glitch = {"burst": 0, "frame": 0, "next": time.monotonic() + 1.5}
    running = {"active": True}

    def update_glitch():
        if not running["active"]:
            return

        now = time.monotonic()
        changed = False

        if glitch["burst"]:
            fx.clearstamps()

            for block in frames[glitch["frame"]]:
                stamp_rect(fx, *block)

            # alternate between the two sets of noise blocks during a glitch.
            glitch["frame"] = 1 - glitch["frame"]
            glitch["burst"] -= 1
            changed = True

            if not glitch["burst"]:
                glitch["next"] = now + 1.0 + rnd(90) / 100

        elif now >= glitch["next"]:
            glitch["burst"] = 4 + rnd(4)
            changed = True

        if changed:
            screen.update()

        if running["active"]:
            screen.ontimer(update_glitch, 100)

    def draw_dialogue_panel():
        panel_pen.clear()
        rect(panel_pen, -252, -153, 694, 144, HUD)
        rect(panel_pen, -250, -155, 690, 140, "#10141a")

    def show(speaker, message, beat_number):
        ui.clear()
        text(ui, -236, -172, speaker, 10, "#7f8a96")

        for row, line in enumerate(message.split("\n")):
            text(ui, -236, -200 - row * 24, line, 14, "#e8edf1")

        update_clock(beat_number)
        screen.update()

    def finish():
        if not running["active"]:
            return

        running["active"] = False
        fx.clearstamps()
        ui.clear()
        clock.clear()

        text(ui, 0, -200, "[ RECORDING INTERRUPTED ]  -  click to continue",
             14, "#e8edf1", align="center")
        screen.update()

        def continue_scene(_x, _y):
            screen.onclick(None)
            on_done()

        screen.onclick(continue_scene)

    def ending():
        draw_cast(("pilot_thinking",))
        draw_dialogue_panel()
        show("HABITAT MONITOR",
             "EXTERNAL TEAM: 02     HABITAT OCCUPANCY: 01", len(BEATS))

        def alone():
            show("PILOT", "Four kilometres out. No one will be back for hours.", len(BEATS) + 1)
            screen.ontimer(open_case, 1800)

        def open_case():
            draw_case(case_pen, True, True)
            show("PILOT", "One dose. Three people. No way home.", len(BEATS) + 2)
            screen.ontimer(remove_vial, 1600)

        draw_cast(("pilot_reminiscing",))

        def remove_vial():
            draw_case(case_pen, True, False)
            show("PILOT", "I'm sorry.", len(BEATS) + 3)
            glitch["burst"] = 9
            screen.ontimer(finish, 1900)

        screen.ontimer(alone, 1700)

    def next_beat(index=0):
        if not running["active"]:
            return

        if index >= len(BEATS):
            ending()
            return

        speaker, message, cast = BEATS[index]
        draw_cast(cast)
        draw_dialogue_panel()
        show(speaker, "", index)
        position = 0

        def type_character():
            nonlocal position

            if not running["active"]:
                return

            position += 1
            show(speaker, message[:position], index)

            if position < len(message):
                screen.ontimer(type_character, 27)
            else:
                # longer dialogue gets a little more time before the next beat.
                pause = int((1.0 + len(message) / 90) * 1000)
                screen.ontimer(lambda: next_beat(index + 1), pause)

        type_character()

    draw_cast(("captain", "specialist"))
    draw_dialogue_panel()
    show("CREW RECORDING", "", 0)
    screen.ontimer(update_glitch, 100)
    screen.ontimer(next_beat, 1300)


if __name__ == "__main__":
    standalone_screen = turtle.Screen()
    standalone_screen.setup(W, H)
    play(standalone_screen, standalone_screen.bye)
    standalone_screen.mainloop()