import turtle
import time
from pathlib import Path


W, H = 900, 600
HUD = "#cfd6dc"
GREYS = ("#e8ecef", "#9aa1aa", "#5b616b", "#2a2e35", "#c9ced4")
ASSET_DIR = Path(__file__).resolve().parent / "assets"

MISSION_SOL = "SOL 020"
EARTH_DATE = "17 NOV 1988"
LOG_ENTRY = "LOG ENTRY > PILOT #03"
START_MINUTES = 21 * 60 + 6


# each beat contains the speaker, dialogue, and the Pilot's current expression.
# even during the recollections, the camera stays on the Pilot.
BEATS = [
    ("PILOT", "This is a local recording. It isn't going to Houston.\n"
     "I just... need to put down what happened.", ("pilot_neutral",)),

    ("PILOT", "The Commander and the Specialist came back from the rover\n"
     "on the fourteenth. They brought the four sample tubes.", ("pilot_explaining",)),

    ("PILOT", "They left the recorder reels behind. The compartment\n"
     "was jammed, and the samples had to come first.", ("pilot_downcast",)),

    ("PILOT", "They knew something was wrong before they even\n"
     "took their helmets off. The medical case was open.", ("pilot_shocked",)),

    ("COMMANDER — RECOLLECTION",
     "Where is the dose? Tell me exactly what you did.",
     ("pilot_grimacing",)),

    ("SPECIALIST — RECOLLECTION", "You took it? You actually administered it?\n"
     "We don't know what it will do to a human being.", ("pilot_pained",)),

    ("PILOT", "I told them I had taken it. I told them I was still\n"
     "alive, still thinking clearly. I said it was working.", ("pilot_explaining",)),

    ("COMMANDER — RECOLLECTION", "You were ordered to leave that case sealed.\n"
     "We are reporting this to Houston. Now.", ("pilot_grimacing",)),

    ("SPECIALIST — RECOLLECTION", "We have to monitor you. We don't know whether\n"
     "the compound is stable, or what it is changing.", ("pilot_pained",)),

    ("PILOT", "They wanted the case secured. They wanted to send\n"
     "a report. They wanted me back under observation.", ("pilot_holding_head",)),

    ("PILOT", "I thought they would take the only thing keeping me\n"
     "alive. I thought they would put me in quarantine.", ("pilot_downcast",)),

    ("PILOT", "The argument became a struggle. I could have stopped.\n"
     "I could have stepped back and let them report it.", ("pilot_grimacing",)),

    ("PILOT", "I didn't stop. I killed them. Both of them.\n",
     ("pilot_crying",)),

    ("PILOT", "I kept telling myself there was no way all three of us\n"
     "could survive. That I was the one who had to live.", ("pilot_head_bowed",)),

    ("PILOT", "On the sixteenth, Earth made its announcement.\n"
     "Artemis Five was lost during Mars orbital insertion,\n"
     "after a NERVA stage failure.", ("pilot_neutral",)),

    ("PILOT", "They said the crew was presumed dead. All three of us.\n"
     "They gave our families an ending.", ("pilot_downcast",)),

    ("PILOT", "I could have sent the truth. I could have told them\n"
     "where we landed, and what I had done.", ("pilot_explaining",)),

    ("PILOT", "But then they would come looking. They would find\n"
     "the Captain. The Specialist. And then they would find me.", ("pilot_head_bowed",)),

    ("PILOT", "The recorder was still on the rover. Those reels proved\n"
     "we landed, and that the mission continued after the failure.", ("pilot_shocked",)),

    ("PILOT", "So I went back to the MARK ROVER. I forced the\n"
     "recorder compartment and destroyed the U-matic reels.", ("pilot_grimacing",)),

    ("PILOT", "I told myself it was for their families. They could\n"
     "remember three lost astronauts, not what happened here.", ("pilot_downcast",)),

    ("PILOT", "I told myself nobody should have to know.\n"
     "That we could be left here, together, in peace.", ("pilot_crying",)),

    ("PILOT", "The rover is quiet now. There is nothing left on those\n"
     "reels for Earth to recover.", ("pilot_pained",)),

    ("PILOT", "They think all three of us died on the way here.\n"
     "Maybe... that's how it should stay.", ("pilot_head_bowed",)),
]


SPRITES = {
    "pilot_neutral": "pilot_neutral.gif",
    "pilot_explaining": "pilot_explaining.gif",
    "pilot_holding_head": "pilot_holding_head.gif",
    "pilot_downcast": "pilot_downcast.gif",
    "pilot_crying": "pilot_crying.gif",
    "pilot_pained": "pilot_pained.gif",
    "pilot_grimacing": "pilot_grimacing.gif",
    "pilot_shocked": "pilot_shocked.gif",
    "pilot_head_bowed": "pilot_head_bowed.gif",
}


_seed = 2024


def rnd(limit):
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
    # main.py owns the window, so this scene only configures and uses it.
    screen.onclick(None)
    screen.title("HAB TERMINAL — LOG ENTRY 03")
    screen.bgcolor("#14171c")
    screen.tracer(0)

    running = {"active": True, "finished": False}

    required_assets = {"habitat_mars_interior.gif"}
    required_assets.update(SPRITES.values())

    for filename in sorted(required_assets):
        screen.addshape(asset(filename))

    bg, cast_pen, panel_pen, ui, fx, clock = (
        pen(), pen(), pen(), pen(), pen(True), pen()
    )

    habitat = pen()
    habitat.shape(asset("habitat_mars_interior.gif"))
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
    text(bg, -414, 232, MISSION_SOL, 18, "#e8edf1")

    for index, (label, value, unit) in enumerate((
        ("PRESSURE", "12.39", "PSI"),
        ("OXYGEN", "20.61", "%"),
        ("TEMP", "21.18", "C"),
    )):
        y = 188 - index * 70
        text(bg, -420, y, label, 11)
        text(bg, -420, y - 30, value, 16, "#e8edf1")
        bg.goto(-318, y - 14)
        bg.dot(42, HUD)
        bg.dot(34, "#171b22")
        text(bg, -318, y - 21, unit, 9, align="center")

    text(bg, -420, -22, "ENVIRONMENT", 11)
    text(bg, 424, 244, LOG_ENTRY, 14, align="right")
    text(bg, 424, 216, "EARTH DATE " + EARTH_DATE, 14, align="right")
    text(bg, -420, -250, "HAB TERMINAL", 16, "#e8edf1")
    text(bg, -420, -280, "LOCAL RECORDING: UPLINK DISABLED", 8)

    rect(bg, 250, 135, 166, 42, "#596575")
    rect(bg, 254, 131, 158, 34, "#171d26")
    text(bg, 262, 114, "LOCAL FILE", 7, "#cfd6dc")
    text(bg, 262, 99, "NOT UPLINKED", 7, "#d18b72")

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
            cast_pen.goto(0, 0)
            cast_pen.stamp()

        else:
            positions = (-165, 155)

            for name, x in zip(names, positions):
                cast_pen.shape(sprite_file(name))
                cast_pen.goto(x + 60, 58)
                cast_pen.stamp()

    def update_clock(beat_number):
        total = START_MINUTES + beat_number
        hours, minutes = divmod(total, 60)

        clock.clear()
        text(clock, 424, 272, "TIME %02d:%02d" % (hours, minutes),
             14, align="right")

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

    frames = (noise_frame(), noise_frame())
    glitch = {"burst": 0, "frame": 0, "next": time.monotonic() + 1.5}

    def update_glitch():
        if not running["active"]:
            return

        now = time.monotonic()
        changed = False

        if glitch["burst"]:
            fx.clearstamps()

            for block in frames[glitch["frame"]]:
                stamp_rect(fx, *block)

            # alternate between two sets of static to make the interference
            # look like a flickering signal rather than a fixed image.
            glitch["frame"] = 1 - glitch["frame"]
            glitch["burst"] -= 1
            changed = True

            if not glitch["burst"]:
                fx.clearstamps()
                glitch["next"] = now + 1.0 + rnd(90) / 100

        elif now >= glitch["next"]:
            glitch["burst"] = 5 + rnd(5)
            changed = True

        if changed:
            screen.update()

        if running["active"]:
            screen.ontimer(update_glitch, 90)

    def finish():
        if running["finished"]:
            return

        running["finished"] = True
        running["active"] = False

        fx.clearstamps()
        ui.clear()
        clock.clear()
        cast_pen.clearstamps()

        draw_dialogue_panel()
        text(ui, 0, -200, "[ END OF LOCAL RECORDING ]  -  click to continue",
             14, "#e8edf1", align="center")
        screen.update()

        def continue_scene(_x, _y):
            screen.onclick(None)
            on_done()

        screen.onclick(continue_scene)

    def ending():
        if not running["active"]:
            return

        draw_cast(("pilot_head_bowed",))
        draw_dialogue_panel()
        show("PILOT", "I don't know who will find this.\n"
             "I only know that nobody on Earth can hear it.", len(BEATS))

        def final_line():
            if not running["active"]:
                return

            draw_cast(("pilot_neutral",))
            draw_dialogue_panel()
            show("PILOT", "I'm still here.", len(BEATS) + 1)
            glitch["burst"] = 12
            screen.ontimer(finish, 2300)

        screen.ontimer(final_line, 2600)

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
                screen.ontimer(type_character, 30)
            else:
                # give longer lines a little more time before showing the next one.
                pause = int((1.25 + len(message) / 75) * 1000)
                screen.ontimer(lambda: next_beat(index + 1), pause)

        type_character()

    draw_cast(("pilot_neutral",))
    draw_dialogue_panel()
    show("PILOT", "", 0)
    screen.ontimer(update_glitch, 90)
    screen.ontimer(next_beat, 1500)


def run_standalone():
    screen = turtle.Screen()
    screen.setup(W, H)
    play(screen, screen.bye)
    screen.mainloop()


if __name__ == "__main__":
    run_standalone()