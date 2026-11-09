# ============================================================
# display

W, H = 800, 600
P = 8                  # size of one pixel block
WORLD = 360            # a full turn around the world, in degrees
COLS = W // P          # 100 columns on screen, giving a 100-degree view

OCHRE, DIM, INK = "#d9a066", "#9a5a30", "#0a0303"
FONT = ("Courier", 15, "bold")
HUD_FONT = ("Courier", 12, "bold")
MSG_FONT = ("Courier", 13, "bold")

STORM_TICK_MS = 90
MAX_GRAINS = 120


# ============================================================
# opening: walking

HORIZON = 40
JUMP_AT = 4            # forward click that triggers the timelapse
RIDGE_AT = 6           # step where the canyon transition starts
SUN_COL = 340
LANDER_COL = 180
FORWARD_PAN = (0 - COLS // 2) % WORLD
SLOPE_HALF = 46        # half the width of the valley wall, in degrees

# each position corresponds to the player's number of steps.
RISE = [0, 0, 10, 28, 46, 66, 86]
LANDER_U = [13, 11, 10, 8, 6, 5, 4]

PAN_FRAMES = 4

# movement and camera settings
WALK_SECONDS = 5
STRIDE_SECONDS = 0.6
BOB_PX = 4
DEPTH_PER_STEP = 0.6
LEG_METERS = [0, 120, 140, 160, 180, 200, 260]
SHOW_ODOMETER = True


# the two palettes use the same keys so the scene can switch between them.
PAL = {
    "morning": dict(
        seed=0, sun_h=70,
        sky=["#a9633c", "#c47e52", "#dc9f70", "#ebc196", "#f0cfa8"],
        ground=["#c58652", "#b8774a", "#a86a40", "#8f5430", "#74401f"],
        mesa="#d6a87e", mesa_l="#e3b98e", far="#c08a5e", far_l="#d09c70",
        near="#a8683e", near_l="#c28250",
        slope="#a9663a", slope_l="#cf8d58", strata="#8a5030",
        sun="#fff0d0", glow="#f4d4a4", halo="#e6b888",
        streak="#8a5030", sand="#e0b080", rock_d="#4a2a1e", rock_l="#7a4a36",
        grain=["#f0d4a8", "#e0b888", "#c89868", "#a87850"]),
    "afternoon": dict(
        seed=500, sun_h=24,
        sky=["#4a2018", "#8a3c25", "#c0683a", "#e0a068", "#e8b27c"],
        ground=["#9a5430", "#8a4a2a", "#7a3e22", "#5e2e18", "#44200f"],
        mesa="#b87a54", mesa_l="#c88a62", far="#9a5c3a", far_l="#ae6e46",
        near="#7a4026", near_l="#92502e",
        slope="#7e4026", slope_l="#a85e36", strata="#5e2c18",
        sun="#ffc890", glow="#e89050", halo="#c0683a",
        streak="#5e2c18", sand="#b87848", rock_d="#2a140c", rock_l="#5a3020",
        grain=["#d9a070", "#b87848", "#8f5530", "#6a3a20"]),
}


# ============================================================
# opening: canyon vista

V_HORIZON = 60
CANYON_RUBBLE = False

# each point is a screen column and its corresponding height.
CANYON_PTS = dict(
    mesa=[(0, 60), (22, 60), (24, 72), (26, 88), (28, 92), (37, 92), (39, 86), (41, 76),
          (43, 66), (44, 60), (47, 60), (49, 70), (52, 78), (54, 74), (56, 66), (58, 60),
          (99, 60)],
    massif=[(0, 40), (43, 40), (44, 60), (48, 70), (51, 88), (54, 100), (57, 118),
            (60, 128), (63, 126), (66, 140), (69, 152), (72, 150), (75, 164), (78, 174),
            (80, 178), (82, 166), (84, 150), (86, 168), (89, 172), (92, 160), (94, 150),
            (96, 170), (99, 186)],
    wall=[(0, -300), (44, -300), (45, -200), (48, -150), (51, -118), (54, -92), (57, -70),
          (61, -44), (65, -20), (69, 0), (73, 14), (77, 26), (81, 40), (85, 46),
          (88, 56), (92, 60), (95, 70), (99, 80)],
    outcrop=[(0, 80), (3, 84), (5, 70), (8, 60), (10, 40), (13, 22), (16, 2), (19, -18),
             (22, -44), (26, -70), (30, -100), (34, -128), (38, -150), (41, -170),
             (44, -192), (46, -300), (99, -300)],
)

CANYON = dict(
    sky=["#9c6a5c", "#b98672", "#d6aa8a", "#ecd0b0"],
    basin=["#e0c2a6", "#d3ae92", "#bd917a", "#9c6e58"],
    sun=[(11, "#dcb496"), (8, "#e8c8a8"), (5, "#f4dcc0"), (3, "#fff4dc")],
    mesa=("#e4cab0", "#d3b49c"),
    massif=dict(crest="#eab88e", lit="#d98d5e", high="#b86a48", low="#8a4634",
                dark="#5c2a20", seam="#6e342a", gully="#5a2820", haze="#cfa088"),
    wall=dict(crest="#e48a5c", lit="#c8663f", high="#a8503a", low="#6e2a1e",
              dark="#46190f", seam="#52211a", gully="#4a1a12", haze="#a06a58"),
    outcrop=dict(crest="#ee9a6c", lit="#d4724a", high="#b8583a", low="#7a2e1c",
                 dark="#4a1a10", seam="#5a2216", gully="#4a1a12", haze="#a06a58"),
    rubble=("#e28a5c", "#b4562f", "#76301c", "#3e170d"),  # light, mid, dark, shadow
    grain=["#f2d6bc", "#e2bc9c", "#c99a7c", "#a87a60"],
)


# ============================================================
# opening: text

CLOCKS = ["09:12", "09:13", "09:15", "09:16", "09:17", "13:52", "17:41"]
POST_JUMP_CLOCK = "11:17"

WALK_MSG = "System: Walking..."
FORWARD_MSGS = [
    "", "System: Terrain nominal. Proceeding.",
    "System: Wind 18 m/s. Audio input: 0 dB.",
    "System: Slope detected ahead. Gradient +9 deg.",
    "System: Gradient +14 deg. Valley wall ahead.",
    "System: Clock resynchronised. Elapsed: 2 h 35 min. Steps taken: 1.",
    "System: Elevation rising...",
]

BOOT = [
    "MARS-OPS // SENSORY LOG v1.05",
    "> link ........ established",
    "> operator ..... [NO DATA]",
    "> location ..... Mars, surface, Sol 0001",
    "> audio ........ no carrier",
    "> click anywhere to advance",
]

TITLE = "MARS-OPS // SENSORY LOG"
TIMELAPSE_TEXT = "[ 2 HOURS OF WALKING LATER... ]"
AFTER_JUMP_MSG = "System: Elapsed time and odometer do not agree."
LOOK_BACK_MSG = "System: Landing craft in range. Hatch open. Telemetry: no response."
FACE_FORWARD_MSG = "System: Heading restored."
TURNING_MSG = "System: Rotating chassis..."
VISTA_MSG = "System: Terrain scan complete. Biosignatures: none."

FINAL_LINES = ["Four thousand kilometres of canyon. No other footprints.",
               "You are alone here. The silence feels occupied."]
END_CARD = "[ END OF OPENING SEQUENCE ]"


# ============================================================
# opening: turning back

TURN_BACK_HINT = "[ TURN BACK ]"
TURN_BACK_MSG = "System: Proximity alert. Reversing heading."
NO_LANDER_MSG = "System: Lander out of visual range"


# ============================================================
# chase (chapter 2)

GAP_MAX = 8                # 0 means the entity has caught up
CATCH_EVERY = 3            # it gets one level closer every three strides
IDLE_SECONDS = 3.5         # it also gets closer if you stand still for this long

RUN_SPEED = 2.2            # maximum stride rate, in strides per second
MAX_QUEUE = 3              # maximum number of queued clicks
METERS_PER_STRIDE = 9
METERS_PER_GAP = 45        # distance represented by one gap level

DESCENT_SECONDS = 4.5
DESCENT_STEPS = 2.0
MONSTER_U = [22, 14, 11, 9, 7, 6, 5, 4, 3]

FLICKER_SECONDS = 2.8
RAD_NORMAL, RAD_BASE, RAD_STEP = 41, 3200, 1100

CLIFF_MSG = "System: Heading 180. Gradient -14 deg."
CLIFF_HINT = "[ STEP DOWN ]"
DESCENDING_MSG = "System: Descending..."

SIGHTING_MSG = "System: WARNING. High levels of radioactivity detected."
SIGHTING_MSG2 = "System: Source unidentified. Visual: 2 red emitters. Closing."

TURN_RIGHT_HINT = "[ TURN RIGHT ]"
TURN_RIGHT_MSG = "System: Evasive heading. Run."

RUN_HINT = "[ CLICK TO RUN ]"
RUN_MSG = "System: Radiation rising."
RUN_MSG_CRITICAL = "System: Radiation critical. Do not stop."

SOURCE_MSG = "System: Source at %d m."
CAUGHT_MSG = "System: Contact."

LOST_LINES = ["> link ........ LOST", "> audio ........ no carrier",
              "> operator ..... [NO DATA]", "", "SIGNAL LOST"]

NO_SIGNAL_TEXT = "OLD TAPES FOUND.."
NO_SIGNAL_FRAME_MS = 70