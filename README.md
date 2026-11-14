# Oblivion on PS4 — OBSE, controller support, no more "unknown version"

Everything needed to run **The Elder Scrolls IV: Oblivion** with **OBSE** and a
**gamepad** on a jailbroken PS4, through [Playden for PS4][playden-ps4].

Oblivion on Playden almost works — the game starts and is playable. What does
not work out of the box is **OBSE** (and therefore every mod that needs it,
including the controller mod). Two separate things break it:

1. Playden rewrites `Oblivion.exe` when it prepares the game, which changes the
   file's **Adler32**. OBSE identifies the game by that checksum, so it reports
   *"You have an unknown version of Oblivion"* and refuses to load.
2. OBSE normally starts the game through `obse_loader.exe`, which launches it
   **suspended** so it can inject code. This runtime refuses that, and the loader
   dies with `Launching Oblivion failed (code = 00000032 (50))`.

This repo fixes both — the game loads OBSE itself, and the checksum is corrected —
and it survives Playden's automatic **check-and-repair**, which would otherwise
revert any patched exe before every launch.

| | |
|---|---|
| Game | Oblivion GOTY, [Steam app 22330](https://store.steampowered.com/app/22330/) |
| Runtime | [Playden for PS4][playden-ps4] (tested on `ps4-v0.2.0`) |
| OBSE | 0021, `obse_1_2_416.dll` — [obse.silverlock.org](https://obse.silverlock.org/) |
| Controller | [NorthernUI](https://www.nexusmods.com/oblivion/mods/48577) (optional) |
| Console | PS4 on GoldHEN (any firmware GoldHEN supports) |

---

## Contents

- [What you need](#what-you-need)
- [1. Playden on your PS4](#1-playden-on-your-ps4)
- [2. Oblivion through Playden](#2-oblivion-through-playden)
- [3. Turn on FTP](#3-turn-on-ftp)
- [4. Grab OBSE and NorthernUI](#4-grab-obse-and-northernui)
- [5. Run the installer](#5-run-the-installer)
- [6. Tell Playden what to start](#6-tell-playden-what-to-start)
- [Did it work?](#did-it-work)
- [After Playden repairs or updates](#after-playden-repairs-or-updates)
- [Controller setup](#controller-setup)
- [Troubleshooting](#troubleshooting)
- [Uninstalling](#uninstalling)
- [How it works](#how-it-works)
- [FAQ](#faq)
- [Credits](#credits)

---

## What you need

- A **jailbroken PS4** running **GoldHEN** (GoldHEN also provides the FTP server
  the installer uses).
- **Oblivion** bought on **your Steam account**. Playden does not pirate games;
  it downloads what your account owns.
- A **PC on the same network** with **Python 3.8+**. That is where the installer
  runs — it never runs on the console.
- About 10 minutes.

You do **not** need: a Windows PC, Wine, a mod manager, a USB stick, or any
knowledge of hex editors.

---

## 1. Playden on your PS4

Playden is what runs Windows games on the console. The PS4 version is a separate
project from the PS5 one:

> **[github.com/plastikman/playden-ps4][playden-ps4]** — installs and updates: see its
> [Releases][playden-ps4-releases] page.

1. Download `IV0000-PLDN10001_00-PLDN100010000000.pkg` from the latest release
   (`ps4-v0.3.0` at the time of writing).
2. Install it with **GoldHEN's package installer**.
3. Start **Playden for PS4** and **sign in to Steam** (QR code, or username and
   password with Steam Guard). The session is cached between runs.

Playden keeps its data in `/data/PLDN10001` — games, Wine prefixes, settings,
save backups. Newer packages install over the old one and your data stays.

> Playden for PS4 is **alpha software**. It signs in to your real Steam account,
> downloads games with your licenses and reads/writes your Steam Cloud saves.
> Read its README before you start and report PS4 problems to the **PS4** repo,
> not the PS5 project.

Upstream, for context: [Playden for PS5](https://github.com/leolobato/playden-ps5)
and [Orbis-Win](https://github.com/plastikman/orbis-win), the Wine/DXVK layer the
PS4 package carries.

---

## 2. Oblivion through Playden

1. In Playden, open your **library**, find **The Elder Scrolls IV: Oblivion Game
   of the Year Edition**, and install it. It downloads from Steam like any other
   game; only one download runs at a time.
2. **Start it once and let it reach the main menu**, then quit. This makes
   Playden finish setting up the Wine prefix, the game folder and its file
   manifest. The installer needs that folder to exist.
3. Note the game folder if you ever need it by hand — it lives at
   `/data/PLDN10001/games/22330` (22330 is the Steam app id).

The game folder will contain `Oblivion.exe`, `OblivionLauncher.exe`, `Data\`,
and a hidden `.playden-tree` file that lists every file with its SHA-1 and size.
That file is the reason a patched exe normally gets reverted — see
[below](#after-playden-repairs-or-updates).

---

## 3. Turn on FTP

On the PS4, open **GoldHEN settings** and enable the **FTP server**. Defaults:
port **2121**, user `anonymous`, no password. Find the console's IP under
**Settings → Network → View Connection Status**.

Test it from your PC:

```bash
ftp 192.168.1.50 2121     # your console's IP, not this one
```

---

## 4. Grab OBSE and NorthernUI

**OBSE 0021** — <https://obse.silverlock.org/>

Download the archive for Oblivion 1.2.416 and extract it somewhere. You need
`obse_1_2_416.dll`; the installer copies that one file. (`obse_loader.exe` is
*not* used and does not need to work — that is the whole point of this fix.)

**NorthernUI** (optional, gives you gamepad support) —
[NexusMods mod 48577](https://www.nexusmods.com/oblivion/mods/48577). Download the
main file and extract it; you need `NorthernUI.dll`, `NorthernUI.ini`,
`NorthernUI.ctrl.txt` and `NorthernUI.l10n.txt`. Source lives at
[DavidJCobb/NorthernUI](https://github.com/DavidJCobb/NorthernUI); it is
compatible with official OBSE 0021.

Neither file is included here — they belong to their authors. Download them from
the links above.

---

## 5. Run the installer

```bash
git clone https://github.com/shitastical/oblivion-ps4
cd oblivion-ps4
pip install -r requirements.txt
python install.py --obse /path/to/OBSE0021 --northernui /path/to/NorthernUI
```

On Windows you can also double-click `install-windows.bat` (edit the paths inside
it first, or just run the command above in a terminal).

It asks for your console's IP if you do not pass `--host`, then:

```
connected to 192.168.1.50:2121
  game folder: /data/PLDN10001/games/22330
downloading the game exe Playden runs ...
  got 7549440 bytes, crc 7934C86C (retail 1.2.0.416 ...)
  patched: OBSE section added, checksum corrected
uploading ...
  Oblivion.exe + OblivionLauncher.exe  sha1 7475859baf5bb7bf
  manifest synced
  installed obse_1_2_416.dll
  installed NorthernUI.dll (and .ini, .ctrl.txt, .l10n.txt)
  verified Oblivion.exe           ok
  verified OblivionLauncher.exe   ok
```

What it did:

- downloaded **your** game exe from **your** console (no game files ship with
  this repo),
- appended a small `.obse` section that loads `obse_1_2_416.dll` at startup and
  jumps to the real entry point,
- recomputed the Adler32 so OBSE sees retail 1.2.0.416,
- uploaded the result as **both** `Oblivion.exe` and `OblivionLauncher.exe`
  (Playden's recipe can start either name),
- rewrote those two rows in `.playden-tree` so Playden's verify finds nothing to
  restore,
- if you passed `--obse` / `--northernui`: installed the DLLs, created
  `Data\OBSE\Plugins`, and wrote `Data\OBSE\obse.ini` with crash dumps on.

Options: `--host IP`, `--port 2121`, `--game /data/PLDN10001/games/22330`,
`--redeploy`, `--keep`. Run it twice if you like — it detects an already-patched
exe and only re-uploads and re-syncs.

---

## 6. Tell Playden what to start

In Playden: **Oblivion → Options / Game settings → Program → `Oblivion.exe`**,
then **Play**.

Both names are the patched build, so either choice ends up in the same place. The
button may say **PLAY (repairs first)** — that is expected and fine now; the
repair has nothing to correct.

---

## Did it work?

Play the game for a moment, quit, then look in the game folder for **`obse.log`**
(FTP, or any file browser). A working log ends like this:

```
OBSE: initialize (version = 21.4 010201A0)
oblivion root = Z:\data\PLDN10001\games\22330\
config path = ...\Data\OBSE\obse.ini
plugin directory = ...\Data\OBSE\Plugins\
patched
```

`patched` means OBSE hooked the game. `Data\OBSE\Plugins\` (not `OBSE\Plugins\`)
is where it looks for plugins, so NorthernUI must be there — the installer puts
it there.

`obse_loader.log` is from the old launcher and stops being written. Ignore it,
and ignore `obse_loader.exe` in the folder; nothing starts it.

---

## After Playden repairs or updates

Playden stores a SHA-1 and size for every file in `.playden-tree` and restores
anything that does not match, before every launch. That is a feature (it repairs
broken installs) and it is why a plain patched exe gets reverted.

The installer already told the manifest about the patched exe, so ordinary
launches leave it alone. But two things reset it:

- you press **Check and repair files**,
- Playden **updates** or reinstalls the game, or you **recreate the bottle**.

In either case, re-apply in two seconds:

```bash
python install.py --redeploy
```

That re-uploads the build saved in `work/` and rewrites the manifest rows. No
download, no re-patching, no touching the game files by hand. Plugins in
`Data\OBSE\Plugins` are untouched by repairs and do not need reinstalling.

---

## Controller setup

Oblivion has **no** native gamepad support. NorthernUI is the mod that adds it,
with Skyrim-style menus, analogue movement and PlayStation button icons.

`config/NorthernUI.ini` in this repo is a ready-made config for a DualShock 4 /
DualSense. The lines that matter:

```ini
bUsePlaystationButtonIcons=TRUE
bEnhancedMovement360Movement=TRUE
iEnhancedMovementCameraMode=0
```

The installer copies that file to `Data\OBSE\Plugins\NorthernUI.ini`. If you want
to change bindings, edit it there (or `config/NorthernUI.ini` here and re-run
with `--northernui`). `NorthernUI.ctrl.txt` lists every action; the `.l10n.txt`
file provides the on-screen labels.

Combine with Playden's own per-game **controller mode** setting if you want the
console's gamepad API involved; NorthernUI reads the pad directly through OBSE
and works with Playden's default.

---

## Troubleshooting

| What you see | What it means |
|---|---|
| *"You have an unknown version of Oblivion"* | The console's exe is the original one again — a repair or update reverted it. `python install.py --redeploy`. |
| No `obse.log` at all | Playden started a different program. Set **Program** to `Oblivion.exe`. If the folder has a third exe (a crack, a wrapper), point at `Oblivion.exe`. |
| `obse.log` exists but ends with an error | Read the last lines; it names the DLL or plugin that failed. With `bCreateCrashDump=1` (default here) a dump lands next to it. |
| Game crashes instantly, no window | The exe layout is not the one this patcher expects. Run `python tools/check_crc.py <your exe>` and compare with the README of this repo; if the entry point or import table moved, do not guess — open an issue with the numbers. |
| NorthernUI loads but the pad does nothing | The plugin is in the wrong folder. It must be in `Data\OBSE\Plugins\`, which `obse.log` prints. |
| Menus are tiny / stretched | That is Oblivion's UI at 1080p; NorthernUI's own settings can scale it. |
| Installer cannot connect | GoldHEN's FTP server is off, the IP is wrong, or port 2121 is not open. `ping` the console first. |
| Installer says `no game folder found` | Oblivion is not installed yet, or was never started once. Do [step 2](#2-oblivion-through-playden). |
| Installer stopped at `crc = ...` and refused | It downloaded an exe it does not recognise instead of patching blind. That is deliberate — patching an unknown layout would corrupt the game. |

Log a bug with: the installer's output, `obse.log`, and `tools/check_crc.py`
output. Those three answer almost everything.

---

## Uninstalling

The game folder's own repair is the cleanest reset:

```bash
# in Playden: Oblivion → Options → Maintenance → Check and repair files
```

That restores the original `Oblivion.exe` and `OblivionLauncher.exe`, which stops
OBSE from loading (the game itself still runs). Then delete
`Data\OBSE\Plugins\NorthernUI.*` and, if you want, `Data\OBSE\` entirely. Nothing
outside the game folder was modified.

---

## How it works

Three parts, all mechanical, no memory patching at runtime:

**1. Self-loading instead of a launcher.** The patcher appends a `.obse` section
and points the entry point at a stub:

```
pushad
push  "obse_1_2_416.dll"
call  [<IAT slot for LoadLibraryA>]
popad
jmp   <real entry point>
```

OBSE is a DLL whose `DllMain` hooks the game as it starts. Loading it from inside
the game's own process means **no `CreateProcess`** — nothing for the runtime to
refuse.

**2. The checksum.** OBSE hashes the exe with **Adler32** (after clearing the
large-address-aware bit at file offset `0x13E`) and looks the result up in a
version table. The patch appends an overlay whose bytes are solved so that:

```
Σ y_i          ≡ Δa   (mod 65521)
Σ (L − i) y_i  ≡ Δb   (mod 65521)
```

which lands the hash exactly on `0x7934C86C` — retail 1.2.0.416, the entry that
uses `obse_1_2_416.dll` and takes the normal desktop code path. Note it is
Adler32, not CRC32; a "fix the CRC" approach does nothing.

**3. The manifest.** Playden's `.playden-tree` holds one line per file with its
SHA-1 and size. Uploading a patched exe without updating those lines means the
next verify puts the original back. So the installer rewrites exactly two rows.

Playden's own rewrite of the exe ("de-stub") is harmless here: it removes the
`.bind` section and moves the entry point, but every other section keeps its RVA
and bytes, so OBSE's hardcoded addresses stay valid.

Deeper detail — offsets, the IAT lookup that `pefile` gets wrong here, the
overlay solver, the FTP/manifest code — is in [docs/TECHNICAL.md](docs/TECHNICAL.md).

---

## FAQ

**Can I just use `obse_loader.exe`?** No. It starts the game suspended, which this
runtime rejects with error 50 (`ERROR_NOT_SUPPORTED`). Playden upstream tracked
the same failure for Fallout 3, Morrowind and FF7 as
[issue #361](https://github.com/leolobato/playden-ps5/issues/361) and fixed it in
later builds; the PS4 port at the version tested here predates that, and PS4
builds may still refuse it. This repo sidesteps the question entirely by removing
the launcher from the chain.

**Will this break Steam Cloud saves?** No. Saves are written by the game normally,
and Playden syncs them as usual. The exe change is invisible to that.

**Does it work with other mods?** Anything that needs OBSE does, as long as it is
installed in the right place. Textures and meshes (OMM, Wrye Bash output, or just
copied files) go in `Data\` as usual. Plugins with their own DLLs go in
`Data\OBSE\Plugins\`.

**Can I use a different OBSE version?** The patch targets OBSE 0021's version
table. Newer/older versions have different tables and would need another
checksum value — `tools/check_crc.py` and `tools/obse_crc.py` are there to work
that out.

**Does this work on PS5?** The technique is runtime-independent; only the paths
and the manifest differ. This repo targets the PS4 port. If the PS5 port already
fixed launchers (issue #361), plain `obse_loader.exe` may simply work there.

**Is my game exe uploaded anywhere?** No. It moves between your console and your
PC. This repo ships no Bethesda files, no OBSE binaries, no NorthernUI binaries.

**Why both exe names?** Playden's recipe for Oblivion starts
`OblivionLauncher.exe` on some setups. Making both names the patched build means
the game works whichever one it picks.

---

## Credits

- **Bethesda Softworks** — Oblivion. No game files are distributed here.
- **OBSE** — Ian Patterson, Stephen Abel, Paul Connelly and the OBSE team.
  <https://obse.silverlock.org/>
- **NorthernUI** — David JCobb. <https://www.nexusmods.com/oblivion/mods/48577>
- **[Playden for PS4][playden-ps4]** — plastikman's port; **[Playden for PS5](https://github.com/leolobato/playden-ps5)**
  by Leo Lobato; **[Orbis-Win](https://github.com/plastikman/orbis-win)**.
- The patcher, installer and docs in this repo were written for this problem and
  are released under the [MIT license](LICENSE).

[playden-ps4]: https://github.com/plastikman/playden-ps4
[playden-ps4-releases]: https://github.com/plastikman/playden-ps4/releases
