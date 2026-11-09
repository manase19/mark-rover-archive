# MARS-OPS // SENSORY LOG — Developer Guide

A pixel-art horror ARG prototype built with nothing but Python's standard library
(`turtle`, `math`, `random`, `time`). This guide explains how every part works so you can
change the opening and build the next section yourself.

**Contents**

1. [Quick start](#1-quick-start)
2. [The files](#2-the-files)
3. [The mental model](#3-the-mental-model)
4. [The opening sequence, step by step](#4-the-opening-sequence-step-by-step)
5. [Reference: `config.py`](#5-reference-configpy)
6. [Reference: `engine.py`](#6-reference-enginepy)
7. [Reference: `art.py`](#7-reference-artpy)
8. [Build the next section (tutorial)](#8-build-the-next-section-tutorial)
9. [Recipes](#9-recipes)
10. [Gotchas](#10-gotchas)
11. [Troubleshooting](#11-troubleshooting)
12. [Sharing it as open source](#12-sharing-it-as-open-source)
13. [Cheat sheet](#13-cheat-sheet)
14. [Chapter 2: the chase (`chase.py`)](#14-chapter-2-the-chase-chasepy)

---

## 1. Quick start

Put the five `.py` files in one folder and run:

```
python main.py
```

You need Python 3 with `tkinter` (turtle is built on it). The python.org installers include it.
On Debian/Ubuntu: `sudo apt install python3-tk`.

| Input | What it does |
|---|---|
| Click anywhere | Walk forward (the only on-screen option) |
| `B` or `Down` | Hidden: turn 180° and look back at the lander. Press again, or click, to face forward |

The sequence: terminal boot text → six forward clicks (a timelapse hits on click 4) →
a canyon vista in a dust storm → end card.

---

## 2. The files

| File | Job | Knows about the story? |
|---|---|---|
| `main.py` | Builds the game and starts it (about 10 lines of real code) | Only which chapters exist |
| `config.py` | Every number, palette and line of text. **No logic.** | Data only |
| `engine.py` | Reusable core: drawing, effects, wind storm, HUD, `Scene` and `Game` | **No** |
| `art.py` | Landscape toolkit: view maths, ground clutter, angular cliffs | **No** |
| `opening.py` | Chapter 1: the boot, the walk, the timelapse, the canyon | Yes |
| `chase.py` | Chapter 2: step down the cliff, the entity, the run, signal lost | Yes |

The first five are the core. Every further chapter is one more file like `chase.py`.

**Imports only point one way**, so nothing gets tangled:

```
main.py  →  chase.py  →  opening.py  →  art.py  →  engine.py  →  config.py
```

(Each file also imports `engine` and `config` directly.) `chase.py` reuses `opening.draw_walk`. Never import `opening` or `chase` from
`engine` or `art`. If you need something in both, move it down a level.

---

## 3. The mental model

### 3.1 Coordinates

`turtle` puts `(0, 0)` in the **centre** of the window, with **y increasing upward**.

```
              y = 300
   ┌──────────────────────────────┐
   │  top HUD bar    y 268..300   │
   │                              │
   │  x = -400  ····  x = +400    │   the scene lives between
   │          (0,0) centre        │   y = -256 and y = 268
   │                              │
   │  bottom HUD bar y -300..-256 │
   └──────────────────────────────┘
              y = -300
```

In the canyon scene a black caption strip covers `y -254..-190`, so the visible picture there
ends at `y = -190`.

### 3.2 Pixels and columns

Everything is drawn from filled rectangles (`rect`) on an 8-pixel grid (`P = 8`).

* The screen is **100 columns** wide (`COLS = 800 // 8`). Column `i` starts at
  `x = -400 + i * 8`; the helper `art.X(i)` does that sum.
* The world is a **360-column loop** (`WORLD = 360`), so **1 column = 1 degree of heading**.
  The screen shows a 100° slice of it, and `state["pan"]` is the heading of the screen's
  left edge. Turning 360° wraps back to where you started.
* Heights are snapped to the grid with `q(v)`, which keeps everything chunky.

### 3.3 Pens and layering (read this one!)

The engine has five "pens", each just a separate bucket of drawn items you can clear on its own:

| Pen | Used for |
|---|---|
| `pen` | The world (sky, ground, cliffs, lander). Cleared every frame |
| `ui` | HUD bars and text |
| `wind` | The animated storm grains |
| `fx` | Full-screen black wipes |
| `txt` | Typewriter / fading text |

> **turtle stacks items by *creation time*, not by pen.** Whatever was drawn most recently sits
> on top. That is why `Game.render()` draws world → HUD → storm in that order, and why a wipe
> or fading text must be cleared (`fx.clear()`, `txt.clear()`) before the world is redrawn,
> or the *new* world would paint over it. `Game.go()` does this clean-up for you when you
> switch scenes.

### 3.4 One frame

```
game.render()
  1. pen.clear()                              forget last frame's world
  2. scene.draw(game)                         YOU paint: sky, ground, cliffs... with rect()
  3. draw_hud(scene.hud_info(game))           top bar, message bar, hint box
  4. render_storm(scene.storm(game))          wind grains on top (if the storm is on)
  5. screen.update()                          show it
```

A separate timer redraws just the storm layer every 90 ms, so wind keeps moving between
renders.

### 3.5 State, `busy` and the scene model

* `game.state` is one plain dict shared by everything. Each chapter adds its own keys.
* `game.busy` means "an animation owns the screen". While it is `True`, clicks and keys are
  **ignored**. Whoever starts an animation sets it `True`; whoever finishes it sets it `False`.
* A **`Scene`** is anything the player can be "in": boot screen, walk, canyon, a menu, a cave.
  Scenes only *describe* themselves (`draw`, `hud_info`, `storm`, `on_click`, `on_key`); the
  `Game` object calls them.

### 3.6 Deterministic scenery

The world must not change by itself, so scenery never uses `random`. It uses `rnd(n)`, a hash
that returns the same float for the same integer. Same seed, same rocks, every frame and every
run. (`random` is used only for storm grains, which are *supposed* to be chaotic.)

---

## 4. The opening sequence, step by step

```
Boot ──(typewriter, then 1.6 s)──► Walk ──6 clicks──► Canyon ──(player turns back)──► then(game) = chase.begin
                                     │
                                     └─ click 4: timelapse (wipe → text → afternoon palette)
```

All of this lives in `opening.py`.

### 4.1 `Boot`

A scene with `hud = False`. `enter()` types the `BOOT` lines with `type_lines(...)`, waits
1.6 s, then calls `game.go("walk")`. It never calls `render()`; it only uses the `txt` pen.

### 4.2 `Walk`

The player is a robot standing by its lander. **Each click walks one "leg"** in real time.

`state` keys it uses:

| Key | Meaning |
|---|---|
| `steps` | Clicks made so far (the step we are walking *to*) |
| `travel` | How far along we are, in steps. **Fractional mid-walk** (1.0 → 2.0 during leg 2) |
| `odo` | Odometer, metres |
| `clock_min` | In-game clock, minutes since midnight |
| `pan` / `look` | Heading of the left edge / `0` facing forward, `180` looking back |
| `pal` | `"morning"` or `"afternoon"`, a key into `config.PAL` |
| `msg` | The bottom-bar message |

**The big idea: `draw_walk(st)` is a pure function of `st["travel"]`.** The same code draws a
still frame at `travel = 3.0` and every in-between frame of the walk. To animate, we just
slide `travel` from `n-1` to `n` with an easing curve. All the "walking" feel comes from
making things depend on `travel`:

| Effect | How |
|---|---|
| Ground streams toward you | Rocks and ripples live in **slots** (`art.slot`). Each slot's depth `p` grows with `travel`; at `p = 1` it passes your feet and respawns small on the horizon in a new spot |
| Hills swell, with parallax | `zoom_for(rate, travel, pan)` magnifies each layer about the screen centre. Nearer layers use a bigger rate: mesas `0.03`, domes `0.07`, mounds `0.16`, valley wall `0.10` |
| The slope climbs | `RISE` is a list of slope heights per step; `lerp_list(RISE, travel)` blends between entries |
| Mounds grow | Dome and mound amplitudes include `+ 3 * travel` / `+ 2 * travel` |
| Head-bob | Every half-stride the world pen is shifted down `BOB_PX` pixels (`engine.view["dy"]`) |
| Odometer and clock | Interpolated between the leg's start and end values |

One leg (`Walk.advance`):

1. `steps += 1`, `busy = True`, message becomes "Walking...".
2. `tween(WALK_SECONDS, frame, done)` calls `frame(p, elapsed)` as fast as the machine can
   redraw. Each frame updates `travel / odo / clock_min / view["dy"]` and calls
   `game.render()`. It is **time-based**, so a slow machine shows fewer frames, but a leg
   always lasts `WALK_SECONDS`.
3. `arrive(n)` runs when the leg ends and decides what happens next:
   * **n = 6 (`RIDGE_AT`)** → wait 1.2 s → `to_canyon` (storm off, wipe, wait 0.7 s, `go("canyon")`)
   * **n = 4 (`JUMP_AT`)** → show the message, wait 1.5 s, run the timelapse
   * otherwise → give control back (`busy = False`)

**Timelapse** (`Walk.timelapse`): storm off → black wipe → fade in
`"[ 2 HOURS OF WALKING LATER... ]"` → hold 1.8 s → fade out → switch `pal` to
`"afternoon"`, set the clock to `POST_JUMP_CLOCK`, storm back on, hand control back. The
lander is gone from this point on (`state["lander"] = False`): looking back shows only empty ground and the message "Landing craft not found". The clock then spins from 11:17 to 13:52 during the next leg while the odometer barely moves,
which is the intended "elapsed time and odometer do not agree" creepiness.

**Look-back** (`B` / `Down`): `sweep(target)` turns `pan` 180° in 4 frames (`PAN_FRAMES`) and
shows the lander (`draw_lander`) plus your footprints (`draw_trail`). It is disabled once you
reach the last step. `zoom_for` uses the cosine of the heading, so facing backward *shrinks*
the terrain instead of swelling it.

### 4.3 `Canyon`

A still painting, built back to front (a painter's algorithm), in `draw_canyon()`:

1. Sky bands (`bands`)
2. Sun: stacked `disc`s (`CANYON["sun"]`)
3. Sandy basin bands, sand ripples and three long dunes
4. Far hazy mesas (`layer`)
5. **Massif**: sunlit cliff range with a hazy base (`cliff_face(..., haze_h=56)`)
6. **Wall**: the near cliff on the right
7. **Outcrop**: the near rock on the left
8. *(optional)* faceted rubble on the crests, if `CANYON_RUBBLE = True`
9. Three dust puffs
10. Black caption strip

Then `enter()` turns the storm on with its own settings (denser, with more gust streaks,
grains bunched around cliff height, kept above the caption strip), waits 3.5 s and fades in the
two `FINAL_LINES`. If a next chapter was given (`then`), the scene now **waits for the player to
turn back**: a `[ TURN BACK ]` hint appears, and a click or `B` wipes to black and calls
`then(game)`. With no `then`, the scene ends on its own after 5 s with the end card.

### 4.4 How a cliff is made (the recipe behind the look)

```python
tops = ridge(CANYON_PTS["wall"], seed=13, jag=18)          # 1. silhouette
cliff_face(tops, -300, CANYON["wall"], seed=21, gullies=6)  # 2. rock
```

1. **`ridge(pts, seed, jag, run)`** turns a hand-placed polyline of `(column, height)` points
   into **100 heights**, one per column. It chops the line into short flat runs
   (`run=(1, 3)` columns) and nudges each run up or down by up to `jag * 1.5 / 2` pixels.
   Short runs plus big jag give the stepped, chaotic skyline. Everything is on the 8 px grid.
2. **`cliff_face(tops, floor, pal, ...)`** fills the area between `floor` and the skyline:
   * **Strata**: horizontal bands of uneven thickness, lighter high up, darker low down,
     alternating slightly lighter/darker. Seams between bands are broken into short dipping
     segments so layers look cracked.
   * **Crest cap**: a bright strip along every top edge.
   * **Risers**: where the skyline steps down to the right, a bright strip (facing the sun);
     where it steps down to the left, a dark strip.
   * **Gullies**: diagonal dark cracks that step sideways as they run down the face.
   * **Haze** (`haze_h > 0`): the base fades toward `pal["haze"]` for distance.

To change a cliff, edit its points in `CANYON_PTS`, its colours in `CANYON`, or the `jag`,
`gullies` and `seed` arguments in `draw_canyon()`. Change `seed` to reroll the details
without moving the shape.

---

## 5. Reference: `config.py`

Pure data. If you only want to retune pacing, colours or words, you only need this file.

| Section | Contents |
|---|---|
| **DISPLAY (engine)** | `W, H, P, WORLD, COLS`; colours `OCHRE, DIM, INK`; fonts `FONT, HUD_FONT, MSG_FONT`; `STORM_TICK_MS`, `MAX_GRAINS` |
| **OPENING: walking** | Story beats and walk tuning (below), and the `PAL` palettes |
| **OPENING: canyon vista** | `V_HORIZON`, `CANYON_RUBBLE`, `CANYON_PTS` (ridge points), `CANYON` (colours) |
| **OPENING: text** | Every message, the boot lines, the clocks, the end card |

### Walk tuning knobs

| Constant | Effect |
|---|---|
| `WALK_SECONDS` | Length of one leg. Raise it for a slower, longer walk |
| `STRIDE_SECONDS`, `BOB_PX` | Footstep rhythm and head-bob depth |
| `DEPTH_PER_STEP` | How far the ground slides toward you per leg (0–1 is horizon-to-feet) |
| `LEG_METERS` | Distance covered by the leg that *ends* at step `n` |
| `SHOW_ODOMETER` | Hide the `ODOM` readout |
| `RISE` | Valley-wall height after each step |
| `LANDER_U` | Lander "pixel" size at each step. Bigger number, bigger lander |
| `JUMP_AT`, `RIDGE_AT` | Which click triggers the timelapse / ends the walk |
| `SUN_COL`, `LANDER_COL` | Headings of the sun and the lander |

> **Keep the per-step lists the same length.** `RISE`, `LANDER_U`, `LEG_METERS`, `CLOCKS` and
> `FORWARD_MSGS` are all indexed by step number `0..RIDGE_AT`, so each needs `RIDGE_AT + 1`
> entries (currently 7). If you add a step, add an entry to **all five**.

### Palettes

`PAL["morning"]` / `PAL["afternoon"]` keys:

| Key | Used for |
|---|---|
| `seed` | Changes every rock, ripple and hill (a "new place") |
| `sun_h` | Sun height above the horizon |
| `sky`, `ground` | 5 colour stops each, blended into bands |
| `mesa/mesa_l`, `far/far_l`, `near/near_l`, `slope/slope_l` | Body / lit-top colour of each terrain layer |
| `strata` | Contour lines on the valley wall |
| `sun`, `glow`, `halo` | The three sun discs, centre outward |
| `streak`, `sand` | Sand ripple colours |
| `rock_d`, `rock_l` | Slab and pebble colours (also the lander's shadow) |
| `grain` | Four colours for wind grains |

`CANYON` keys: `sky`, `basin`, `sun` (list of `(radius, colour)`), `mesa` (top, body),
`massif` / `wall` / `outcrop` (cliff palettes, below), `rubble`, `grain`.

A **cliff palette** has eight colours: `crest` (brightest top edge), `lit` (sun-facing
strips and lighter bands), `high` and `low` (top and bottom of the strata gradient), `dark`
(shadow strips and darker bands), `seam` (lines between layers), `gully` (cracks) and `haze`
(distance fade).

---

## 6. Reference: `engine.py`

The reusable core. It never mentions Mars, the lander or the story.

### Maths, colour, noise

| Function | What it does |
|---|---|
| `q(v)` | Snap a height to the 8 px grid |
| `lerp(a, b, t)` | Blend two numbers |
| `ease(t)` | Smoothstep: gentle start and stop |
| `interp(pts, x)` | Height at `x` along a `[(x, y), ...]` polyline |
| `mix(c1, c2, t)` | Blend two hex colours |
| `gradient(stops, n)` | `n` hex colours blended across the stops |
| `minutes("09:12")` / `clock_text(mins)` | Clock string ⇄ minutes |
| `rnd(n)` | Deterministic float 0..1. **`n` must be an `int`** |
| `smooth(x, seed, step)`, `terrain(x, seed, step)` | Looping value noise for hills |

### Drawing

| Function | What it does |
|---|---|
| `rect(t, x, y, w, h, color)` | **The only real primitive.** Filled rectangle, bottom-left corner at `(x, y)`, on pen `t` (usually `pen`). Shifted by the head-bob if `t is pen` |
| `disc(cx, cy, r, color, floor)` | Blocky pixel disc. Meant for suns |
| `bands(stops, top, n, h)` | `n` horizontal gradient bands of height `h`, going down from `top` |
| `layer(tops, c_top, c_body, lit, floor)` | Fill a silhouette from 100 column heights |
| `contours(tops, offsets, color, floor)` | Strata lines that follow a silhouette |
| `puff(x, y, w)` | A wisp of blown dust |

### Effects

| Function | What it does |
|---|---|
| `wipe(done, bars=15, step_ms=35)` | Black scan-line wipe, top to bottom, then `done()` |
| `fade_text(lines, y, font, fg, done=None, fade_out=False)` | Centred text fading in (or out) |
| `type_lines(lines, x, y, font, color, done)` | Terminal typewriter |
| `tween(seconds, on_frame, done=None)` | Real-time animation: calls `on_frame(p, elapsed)` with `p` from 0 to 1 |

All of these are **non-blocking**: they schedule themselves with timers and call your `done`
function when finished. Never write a `while` loop that waits. Chain callbacks instead.

### The storm

`render_storm(cfg, tick)` is called for you. Your scene supplies `cfg` from `Scene.storm()`:

| Key | Meaning |
|---|---|
| `key` | Name. **Changing it reseeds the grains** (do this when you change areas) |
| `colors` | Four hex colours |
| `ymin`, `ymax` | Vertical band grains may fly in |
| `ycenter`, `yspread` | Where grains bunch up |
| `level(gust)` | Function returning density 0..1; `gust` swings 0..1 over time |
| `streaks` | Max number of long gust streaks |
| `count` | *(optional)* number of grains, default `MAX_GRAINS` |

### HUD

`draw_hud(info)` takes the dict your scene returns from `hud_info()`:

```python
dict(top=[(-388, "left", "TITLE"), (0, "center", "HDG 000"), (388, "right", "09:12")],
     msg="System: all quiet.",       # bottom bar
     hint="[ CLICK TO ADVANCE ]")    # boxed hint near the top, or None
```

### `Scene`

Subclass it and override only what you need.

| Member | Called when | Default |
|---|---|---|
| `hud = True` | — | Set `False` for a title card or terminal screen |
| `enter(game)` | `game.go()` switches to this scene | nothing |
| `draw(game)` | Every `game.render()` | nothing |
| `hud_info(game)` | Every render, if `hud` | `{}` |
| `storm(game)` | Every render and storm tick, if the storm is on | `None` (calm) |
| `on_click(game, x, y)` | A click, if `not game.busy` | nothing |
| `on_key(game, key)` | A bound key, if `not game.busy` | nothing |

### `Game`

| Member | What it does |
|---|---|
| `state` | The shared dict |
| `busy` | While `True`, input is ignored |
| `add(name, scene)` | Register a scene |
| `go(name)` | Switch scene. Clears wipes, overlay text, the old HUD and the head-bob first, then calls `enter()` |
| `render()` | Draw one frame (section 3.4) |
| `after(ms, fn)` | Run `fn` later |
| `set_storm(on)` | Turn the storm overlay on or off |
| `start(first, keys=())` | Bind input, enter the first scene, run the main loop |

---

## 7. Reference: `art.py`

The landscape toolkit. It draws onto `pen` and takes colours as arguments, so a new chapter can
paint a different planet.

| Function | What it does |
|---|---|
| `X(i)` | Screen x of the left edge of column `i` |
| `scol(wc, pan, margin)` | Screen column of world column `wc`, or `None` if off-screen |
| `heading(wc)` | Signed degrees from straight ahead |
| `sample(pan, zoom)` | The world column under each screen column when magnified by `zoom` |
| `zoom_for(rate, travel, pan)` | Zoom factor for a scenery layer after `travel` steps |
| `lerp_list(vals, t)` | Value at fractional index `t` of a list |
| `slot(key, travel, rate)` / `rr(key, cyc, k)` | Recycling-depth slots and stable per-slot randomness |
| `draw_ripples(...)`, `draw_rocks(...)` | Streaming sand ripples, slabs and pebbles |
| `ridge(pts, seed, jag, run)` | Blocky skyline from a polyline (section 4.4) |
| `cliff_face(tops, floor, pal, seed, gullies, haze_h)` | Stratified rock wall |
| `chunk(x, y, w, h, cols, seed)` | One angular, fractured boulder. Optional; used by `CANYON_RUBBLE` |

---

## 8. Build the next section (tutorial)

A "section" (chapter) is a Python module that registers a few scenes and gives the game a
`begin(game)` function. We'll make a tiny one: the player arrives at a cave mouth, and a click
plays a line of text. This exact code was run and works.

### Step 1: create `chapter2.py`

```python
"""chapter2.py - the cave mouth."""
from art import cliff_face, ridge
from config import CANYON, FONT, OCHRE, TITLE
from engine import Scene, bands, fade_text

# (column, height) points. The dip in the middle is the cave mouth.
CAVE_PTS = [(0, 120), (30, 150), (44, 70), (56, 70), (70, 160), (99, 130)]


class Cave(Scene):
    def enter(self, game):
        game.state["msg"] = "System: Thermal anomaly ahead."
        game.busy = False                 # the previous chapter left this True
        game.render()

    def draw(self, game):
        bands(CANYON["sky"], 300, 12, 20)
        cliff_face(ridge(CAVE_PTS, seed=4, jag=10), -300, CANYON["wall"],
                   seed=9, gullies=4)

    def hud_info(self, game):
        st = game.state
        return dict(top=[(-388, "left", TITLE)], msg=st["msg"],
                    hint=None if game.busy else "[ CLICK TO LISTEN ]")

    def on_click(self, game, x, y):
        game.busy = True                  # ignore clicks while the text plays
        game.state["msg"] = "System: Audio input: 31 dB."

        def done():
            game.busy = False
            game.render()

        fade_text(["Something in the dark is breathing."], 0, FONT, OCHRE, done)


def begin(game):
    game.add("cave", Cave())
    game.go("cave")
```

### Step 2: hook it up in `main.py`

```python
import engine
import opening
import chapter2                                    # new

if __name__ == "__main__":
    game = engine.Game()
    first = opening.install(game, then=chapter2.begin)   # new: then=...
    game.start(first, keys=("b", "Down"))
```

`then` is called with `game` once the player turns back and the wipe has finished. (This repo's
`main.py` already passes `chase.begin`; to try this tutorial, swap in your own chapter.) If you
want a pause before your scene, wait inside `begin`:

```python
def begin(game):
    game.add("cave", Cave())
    game.after(2500, lambda: game.go("cave"))
```

### Step 3: the checklist for every new scene

1. Subclass `Scene` and override `draw`, `hud_info`, `on_click`, as needed.
2. In `enter()`, set `game.busy = False` (when the player should be able to act) and call
   `game.render()` so something appears.
3. Anything that takes time (text, a wipe, a walk) is a callback chain. Set `game.busy = True`
   when you start and `False` in the last `done`.
4. Register with `game.add(name, scene)` and switch with `game.go(name)`.
5. Put colours and text in `config.py` (or a section of your own), not inline.

### Testing without clicking through the whole opening

Temporarily start at your own chapter in `main.py`:

```python
game.add("cave", chapter2.Cave())       # instead of opening.install(...)
game.start("cave", keys=("b", "Down"))
```

If you do this, remember `opening.install()` also sets up `game.state` keys (`pan`, `odo`,
`clock_min`, ...). Set any you use yourself.

---

## 9. Recipes

**Change a line of text** → edit the matching constant in `config.py` (`FORWARD_MSGS`, `BOOT`,
`FINAL_LINES`, `END_CARD`...).

**Make the walk longer or shorter** → `WALK_SECONDS` (time per leg) and `LEG_METERS` (metres per leg).
To make it feel like a longer distance without waiting longer, raise `DEPTH_PER_STEP`.

**Add a fourth walking leg beyond step 6** → raise `RIDGE_AT`, then add one entry to each of
`RISE`, `LANDER_U`, `LEG_METERS`, `CLOCKS`, `FORWARD_MSGS`.

**Add a new time of day** → copy `PAL["afternoon"]` to `PAL["night"]`, change the colours and
`seed`, and set `game.state["pal"] = "night"` when it should happen.

**Run something after a delay** → `game.after(1500, lambda: ...)`.

**Change scenes with a wipe** →
`wipe(lambda: game.after(700, lambda: game.go("name")))`.

**Add a HUD readout** → append `(x, "right", "TEXT")` to the `top` list your `hud_info`
returns. The top bar text sits at `y = 274`. Keep to the free gaps in the bar (see `top_bar`
in `opening.py`).

**Add wind to a new scene** → return a storm `cfg` from `Scene.storm()` and call
`game.set_storm(True)` in `enter()`. Use a new `key`.

**Paint a new cliff scene** → copy `draw_canyon()`, replace the point lists in `CANYON_PTS`,
retune the palettes, and reroll `seed`.

**Turn the odometer off** → `SHOW_ODOMETER = False`.

**Bring back boulders on the cliffs** → `CANYON_RUBBLE = True`.

---

## 10. Gotchas

* **Layering is by creation time.** Clear `fx`/`txt` before redrawing the world, or the old
  overlay is painted over by the new frame. (`go()` does this for scene switches.)
* **`busy` stays `True` until you reset it.** If clicks suddenly do nothing, some animation
  forgot to set `game.busy = False` in its final callback. This is the number one bug.
* **`rnd()` needs an integer.** `rnd(3.5)` raises a `TypeError` (it uses bit operations).
  Wrap with `int(...)`.
* **Don't use `random` for scenery.** It makes the world flicker between frames. Use `rnd` with
  a seed.
* **Never call `screen.update()` inside `draw()`.** `render()` already does it once per frame.
* **Heights are screen y, not "height above ground".** A skyline `ridge` point of `(50, -100)`
  is 100 px *below* the screen centre.
* **Keep the draw cost down.** Each `rect` costs a few turtle calls. Roughly 1,500 rects per
  frame is where slower machines start to drag. The loops in `art.draw_rocks`
  (`count=130`) and `art.draw_ripples` (`count=140`) are the first things to lower.
* **Time-based, not frame-based.** Use `tween`, never "move 5 px per frame", so animation speed
  doesn't depend on the machine.
* **Per-step lists must match** `RIDGE_AT + 1` in length (section 5).
* **Dependency direction:** `config ← engine ← art ← opening ← main`. Don't import upward.

---

## 11. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `ModuleNotFoundError: tkinter` | Install Tk: `sudo apt install python3-tk` (Linux), or reinstall Python from python.org |
| Window opens, nothing happens on click | `game.busy` is `True`. Check your last `done()` callback sets it `False` |
| Old text or black bars stuck on screen | You drew a wipe/text outside `go()` and never cleared `fx`/`txt` |
| New scene looks "dirty" | Switch scenes with `game.go()` (it cleans up), not by assigning `game.scene` |
| Walk is choppy | Lower the `count=` values in `art.draw_rocks`/`draw_ripples`. Duration stays the same |
| `KeyError: 'xyz'` in a palette | A palette is missing a key the drawing function needs. See the key tables in section 5 |
| `IndexError` when walking | A per-step list in `config.py` is shorter than `RIDGE_AT + 1` |
| Clicks work but the key doesn't | Keys must be listed in `game.start(first, keys=(...))` |
| Storm grains look stuck in a line | Two scenes share a storm `key` but have different `ymin`/`ymax`. Give them different keys |

---

## 12. Sharing it as open source

* **No dependencies**: standard library only, so there's nothing to `pip install`.
* **Add a `LICENSE`** (MIT is the usual choice for small game projects). The files don't
  contain one yet.
* **A good `README.md`** can be a trimmed copy of sections 1–3 of this guide, with this
  file kept as `GUIDE.md`.
* **Art references:** the cliffs were hand-built from a reference photo. Don't commit the photo
  unless you have the rights; the colours and point lists in `config.py` are your own work.
* **Contribution-friendly structure:** new chapters are new modules, and content edits are
  mostly in `config.py`, so contributors rarely need to touch `engine.py`.

---

## 13. Cheat sheet

| I want to... | Edit |
|---|---|
| Reword any message | `config.py` text section |
| Slow down / speed up walking | `WALK_SECONDS` |
| Change how far each leg "feels" | `DEPTH_PER_STEP`, `LEG_METERS` |
| Resize the lander | `LANDER_U` |
| Recolour the world | `PAL`, `CANYON` |
| Reshape a cliff | `CANYON_PTS` |
| Make cliffs rougher | `jag=` in `draw_canyon()` (opening.py), `run=` in `ridge` (art.py) |
| Windier / calmer dust | `Walk.storm()` / `Canyon.storm()` `level` and `count` |
| Add a scene | New `Scene` subclass, `game.add`, `game.go` |
| Add a chapter | New module with `begin(game)`; `opening.install(game, then=...)` |
| Tune the chase | Section 14 table (`config.py`, CHASE section) |
| Reuse the engine in another game | Copy `engine.py` + `config.py` display section |

---

## 14. Chapter 2: the chase (`chase.py`)

After the canyon, the player turns back, steps down the slope, meets the entity, turns right
and runs. It cannot be outrun. It is a single scene, `Chase`, driven by `state["phase"]`.

```
cliff ──click──► descend (tween) ──► seen ──click──► turn right ──► run ──► dead
                                       ▲ warning + entity               │      │
                                       │                  B / Down: look back   flicker ──► SIGNAL LOST
```

| Phase | What happens |
|---|---|
| `cliff` | You are on the cliff, facing back toward the plain. `[ STEP DOWN ]` |
| `descend` | A 4.5 s leg. The slope behind the horizon sinks (`state["rise"]` goes 86 → 0), ground streams past. Ends in `sighting()` |
| `seen` | The entity stands ahead, tiny, with two red eyes. `RAD` jumps to 3200 and the bar reads "High levels of radioactivity detected". `[ TURN RIGHT ]` |
| `run` | After a 90° turn, you run. Each click queues a stride; strides play smoothly at `RUN_SPEED` |
| `dead` | `caught()` snaps the view to the entity at full size, then `flicker()`, then `signal_lost()` |

**The entity is a discrete distance.** `state["gap"]` runs from `GAP_MAX` (8) down to 0. It drops one
level every `CATCH_EVERY` strides (so 24 strides in total) **and** every `IDLE_SECONDS` that you stand
still. Facing forward you only see the `RAD` readout rise; press `B`/`Down` and you see the figure
at its current level (`MONSTER_U[gap]` is its size) with the message "Source at N m". It is drawn only when
the view looks at it: `state["mcol"]` is its heading (0 at first sighting, 270 = behind you once you run).

**How the run feels continuous.** `on_click` only raises `state["target"]`; `run_frame` slides
`state["travel"]` toward it each frame (time-based, same trick as the walk), and the existing
`draw_walk` scenery responds to `travel`. The dusk palette is generated from the afternoon one by
`make_dusk()` and registered as `PAL["dusk"]`. The chapter reuses `draw_walk` with three state overrides:
`rise` (valley-wall height), `scenery` (pins how close the hills look) and `dir` (travel heading), plus
`lander=False`.

**Caught.** `flicker()` draws only on the `fx` pen (a few rectangles per frame, so it stays fast):
random horizontal tearing and static, an occasional dark-red flash, and full-black frames that get more
likely over `FLICKER_SECONDS`. Then `signal_lost()` types `LOST_LINES` on black and fades to nothing.

### Tuning (in `config.py`, CHASE section)

| Constant | Effect |
|---|---|
| `GAP_MAX`, `CATCH_EVERY` | Run length: it takes `GAP_MAX * CATCH_EVERY` strides to be caught |
| `IDLE_SECONDS` | How long you may stand still per level lost |
| `RUN_SPEED`, `MAX_QUEUE` | Stride rate; how many clicks may queue ahead |
| `MONSTER_U` | The entity's size at each distance level |
| `METERS_PER_GAP`, `RAD_*` | The look-back distance and the radiation readout |
| `FLICKER_SECONDS` | Length of the glitch before SIGNAL LOST |
| `*_MSG`, `*_HINT`, `LOST_LINES` | All the words |

### Extending it

The easiest next step is a new chapter after `signal_lost`: give `Chase` a `then` like `Canyon` has
(store it in `__init__`, call `self.then(game)` at the end of `signal_lost`), and pass it from `main.py`.
To make the entity different, edit `PARTS` / `EYES` in `chase.py`: each part is `(x0, x1, y0, y1)` in units
of the entity's pixel size.