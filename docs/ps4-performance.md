# Running Oblivion at 60 fps on a PS4 Slim

A starting configuration and a tuning order, for getting a **steady 60 fps that
still looks like Oblivion**. This is a living document: the defaults below are
the well-documented best-value settings for Oblivion on weak hardware, adapted to
what Playden exposes on a PS4 Slim. The tables at the end are for recording what
we actually measure on console, so the preset can be tightened instead of
guessed at.

## The hardware, honestly

| | PS4 Slim |
|---|---|
| CPU | 8-core AMD Jaguar, 1.6 GHz — about a 2013 laptop core |
| GPU | 1.84 TFLOPS GCN, 18 CUs |
| Memory | 8 GB GDDR5, shared with the GPU |
| Output | 1080p, 60 Hz |

Oblivion renders on **one CPU thread**. Its frame time is dominated by draw
calls, actors and grass, not by shader math, so the Jaguar core — not the GPU —
is what decides whether a scene holds 60. That has two consequences:

- **Resolution helps less than you expect.** Dropping 1080p to 720p buys GPU
  time; in a crowded city square the bottleneck is still the CPU.
- **The knobs that cut CPU work win.** Fade distances, grass distance, shadow
  casters and distant LOD remove work from that one thread. They are also the
  knobs that change how the game looks the most, which is the whole tension.

## Why 60 and not higher

Bethesda's engine ticks at a fixed 60 Hz and several systems are tied to it. Above
60 fps Oblivion speeds up: walking gets comically fast, physics goes unstable and
scripts misfire. The community fix is always the same — cap at 60 and let the
display pace it.

- **Do not set `iFPSClamp`.** It looks like the obvious answer and it is not: it
  forces the tick rate and makes time, physics and quests misbehave. Leave it at
  `0` and cap with VSync or the frame limiter instead.
- Playden's **Frame limit** already writes `d3d9.maxFrameRate` into `dxvk.conf`;
  that is the cap to use.

So the target is not "as many fps as possible". It is **60 everywhere, without
dropping frames**, and if a scene cannot hold 60, the fix is to remove work until
it does — not to leave the cap off.

## Playden settings

Oblivion → **Options / Game settings**:

| Setting | Value | Why |
|---|---|---|
| Graphics | **DXVK** | Oblivion is Direct3D 9. DXVK gives the frame limiter and VSync; the other paths are slower or unsupported. |
| Resolution | **1280×720** | The single biggest GPU-side win. 1080p is for after the CPU work is sorted. |
| Refresh rate | **60 Hz** | The PS4 Slim has no 120 Hz mode; Oblivion misbehaves above 60 anyway. |
| Frame limit | **60** | Writes `d3d9.maxFrameRate = 60`. |
| VSync | **On** (or Game default) | Stops tearing. The PS4 display paces presentation regardless, so this is not optional in practice. |
| Scaling | **Fit** | Keeps 16:9 without stretching. |
| Performance overlay | **On** while tuning, off after | DXVK HUD. Read the number in the corner. |
| Program | **Oblivion.exe** | The patched self-loading exe. |

Do not edit `dxvk.conf` by hand: Playden rewrites it from these settings on every
launch. The file in the game folder shows what it currently wrote, which is handy
for confirming the cap is live.

Leave `Oblivion.dxvk-cache` alone. It is the shader cache; deleting it means the
first minutes of play recompile every shader and stutter.

## In-game video settings

Start the game, **Options → Video**. These are the settings that matter, in the
order they cost you frames:

| Setting | Start at | Cost | Notes |
|---|---|---|---|
| Resolution | 1280×720 | high | Match Playden. |
| Texture Size | **Large** | low | Costs video memory, not CPU time. Keep it. |
| Self Shadows | **Off** | high | Actor shadows on themselves. Turning it off is the best-looking frame-rate win in the game. |
| Shadows on Grass | **Off** | high | Only affects actor shadows on grass. |
| Tree Canopy Shadows | **Off** | medium | |
| Shadow Filtering | **Low** | medium | |
| Ext. Shadows | **2** (of 10) | high | Number of actors casting shadows outdoors. |
| Int. Shadows | **2** (of 10) | medium | Same, indoors. |
| Grass Distance | **25%** | very high | Grass is the classic Oblivion frame-rate killer. Below ~25% the ground starts to look bald. |
| View Distance | **50%** | high | `fNoLODFarDistancePct`. Lowering it shrinks what is drawn at all. |
| Object Fade | **50%** | high | Draws fewer small props near you. |
| Item Fade | **40%** | medium | |
| Actor Fade | **50%** | medium | Lower means NPCs pop in late. |
| Tree Fade | **50%** | medium | |
| Distant Land | **On** | low | Turning this off empties the world; keep it. |
| Distant Buildings | **On** | low-medium | Keeps cities on the horizon. |
| Distant Trees | **On** | low-medium | |
| Specular Distance | **50%** | low-medium | Shiny highlights at range. |
| HDR Lighting | **On** | low | Looks much better than Bloom; costs little on this GPU. |
| Bloom Lighting | **Off** | — | Mutually exclusive with HDR. |
| Water Detail | **Medium** | low | |
| Water Reflections | **Off** | high | Renders the scene twice. First thing to re-enable if you have headroom. |
| Water Ripples | **Off** | low | |
| Window Reflections | **Off** | low-medium | |
| Blood Decals | **On** | low | |
| Anti-aliasing | **Off** | medium | At 720p on a TV, skip it; DXVK scaling handles the rest. |

That is the **60 fps starting point**. It should hold 60 in most exteriors and
interiors. Cities and Oblivion gates are the stress cases.

### If it still runs badly after that

Work down this list; each step is a real, visible amount of frame rate:

1. **Playden Resolution → 1024×768.** Ugly (4:3, bars at the sides) but it
   removes the GPU from the conversation, which tells you whether you are CPU
   bound. If fps barely moves, the CPU is the limit and you should go back to
   720p and cut grass, fades and shadows instead.
2. **Grass Distance → 15%.** Nearly the whole grass cost, still some tufts left.
3. **Object Fade and Item Fade → 30%.**
4. **Distant Trees → Off**, then **Distant Buildings → Off**. The horizon gets
   emptier; the city load time and the CPU cost both drop.
5. **Ext. Shadows and Int. Shadows → 0.** Characters stop casting shadows. The
   lighting still works; it looks flatter.

If the overlay shows **60 but the game feels choppy**, that is not a settings
problem — it is frame pacing or shader compilation. Walk the same route twice:
if the stutter fades on the second pass, it was shader compilation and the cache
(`Oblivion.dxvk-cache`) will keep it away. Leave the overlay off when you are not
measuring; the HUD itself costs a little.

### If it holds 60 comfortably, spend the headroom in this order

1. **Water Reflections → On** (biggest visual return).
2. **Grass Distance 35% → 50%**.
3. **Object Fade and Item Fade up 10%** each.
4. **Resolution 1280×720 → 1920×1080** — only if you were GPU-bound, which shows
   up as fps that does not change when you walk into a crowded area. If 1080p
   costs you 10 fps, the CPU was already the limit and you should go back.
5. **Ext. Shadows 3 → 5**, then **Shadow Filtering → Medium**.

Change **one** setting at a time and re-measure. Oblivion's frame time is spiky;
two changes at once tell you nothing.

## How to measure so the numbers mean something

The overlay fps number is an average and lies in both directions. Use the same
three places every time, and watch the number while standing still, then while
walking, then in combat:

1. **Open country** — the road outside the Imperial City, looking across grass.
   This is the grass-and-LOD test.
2. **A city** — the Imperial City Market District, looking down the street with
   NPCs in view. This is the CPU test; resolution barely moves it.
3. **An Oblivion gate** — the first one outside Kvatch, with the sky and fire
   effects on screen. This is the effects test.

Record the lowest number you see in each, not the highest. A stable 55 feels
better than 60 that hitches to 30, and 60-cap-or-nothing is the goal.

### Log

Fill this in on console; it is what the next round of tuning works from.

| Preset | Open country | City | Gate | Notes |
|---|---|---|---|---|
| 720p, settings above | | | | |
| | | | | |
| | | | | |

## What "60 everywhere" realistically means

Oblivion on a 1.6 GHz Jaguar will not hold a locked 60 through the Market
District with the settings that make it look good. Expect:

- **Interiors, dungeons, most wilderness:** 60, easily.
- **Wilderness with heavy grass:** 60 with grass at 35%, dips when you spin the
  camera fast through tall grass.
- **Cities:** the CPU limit. Drop Object Fade and Ext. Shadows first; resolution
  will not save you.
- **Oblivion gates:** effects-heavy; Water Reflections off and Grass Distance low
  are what keep these playable.

If a scene will not hold 60 no matter what, the honest options are a lower
resolution for the blur to hide the dips, or accepting 45–55 in that one place.
Chasing a locked 60 in every city on this hardware costs more of the look than it
is worth.

## Advanced: settings the Video menu does not expose

These live only in `Oblivion.ini` (`My Games\Oblivion\` inside the game's Wine
prefix) and are worth knowing, because a couple are large:

| Key | Default | Try | Effect |
|---|---|---|---|
| `iMinGrassSize` | 80 | **120** | Grass density. Higher = sparser = faster. The single biggest outdoor win after grass distance. |
| `fGrassWindMagnitudeMax` / `Min` | 125 / 5 | **0 / 0** | Stops grass animation; small but free. |
| `bDoSpecularPass` | 1 | leave **1** | Turning it off is said to crash in a few interiors (Weynon Priory, Skingrad courtyard, Anvil castle). Not worth it. |
| `iActorShadowCountExt` / `Int` | 5 / 5 | **3 / 3** | What the Ext./Int. Shadows sliders write. |
| `bUseThreadedBlood`, `iThreads`, `iNumHavokThreads` | — | leave | Widely tested on PC, no measurable gain; not worth destabilising the prefix. |
| `iFPSClamp` | 0 | **0** | See above. |
| `uGridsToLoad` | 5 | **5** | Lowering it breaks LOD and quests. Do not. |

**Why we are not shipping an ini yet:** on this Playden build the prefix
(`.../library/prefixes/game/drive_c/users/.../Documents/My Games/Oblivion/`) is
private to the game and not reachable over GoldHEN's FTP, so the file cannot be
edited from the installer the way `dxvk.conf` can. The Video menu writes the same
keys for everything in the table above except the first three, which is why the
menu is the supported route for now.

If you want the ini-only keys, the engine will read `Oblivion.ini` from the game
folder instead of `My Games` when `bUseMyGamesDirectory=0` is set in that copy —
see the [UESP ini notes](https://en.uesp.net/wiki/Oblivion:Ini_Settings). It also
moves where the game looks for `Plugins.txt` and, depending on `SLocalSavePath`,
where saves land — and Playden syncs saves from the documented location. That is
a save-integrity risk, so it is not part of the default install until it has been
tested end to end on console.

## Sources

- UESP, *Oblivion:Ini Settings* — ini semantics, `bUseMyGamesDirectory`, warning
  that `uGridsToLoad` and `iFPSClamp` changes cause problems.
- Step Modifications, *Guide:Oblivion INI* — which in-game slider writes which
  ini key, and the settings list used above.
- TweakGuides, *Elder Scrolls IV: Oblivion Tweak Guide* — per-setting visual and
  performance comparisons (self shadows, shadows on grass, grass density).
- Bethesda support, *How can I improve the performance of Oblivion?* — official
  list of the settings that matter.
- Community consensus (Steam/Nexus/STEP threads) on the 60 fps cap: physics and
  game speed are tied to the frame rate, `iFPSClamp` makes it worse, cap
  externally.
