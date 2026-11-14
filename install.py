#!/usr/bin/env python3
"""Install OBSE into Oblivion on Playden (PS4/PS5) over FTP.

What it does, in order:

  1. connects to the console's FTP (GoldHEN) and finds the game folder
  2. downloads the Oblivion.exe Playden actually runs (the de-stubbed one)
  3. patches it so it loads obse_1_2_416.dll itself, and forces the Adler32 that
     OBSE accepts (no obse_loader.exe, so no CreateProcess / error 50)
  4. uploads it as both Oblivion.exe and OblivionLauncher.exe
  5. rewrites those rows in Playden's .playden-tree manifest, so its pre-launch
     verify has nothing to "repair"
  6. if you give it the OBSE and NorthernUI folders, copies those in too,
     putting plugins where OBSE 21 actually reads them (Data\\OBSE\\Plugins)

Typical use:

    python3 install.py

After Playden overwrites the folder (Repair / reinstall / update), just run:

    python3 install.py --redeploy

Options:
    --host            console IP                   (prompted if omitted)
    --port            FTP port                     (default 2121)
    --game            game folder on console       (default /data/PLDN10001/games/22330)
    --obse DIR        folder holding obse_1_2_416.dll from the OBSE 0021 archive
    --northernui DIR  folder holding NorthernUI.dll (adds controller support)
    --redeploy        re-upload the saved build without re-downloading anything
    --keep            keep work/Oblivion.console.exe after a successful patch
"""
import argparse
import hashlib
import io
import os
import sys
from ftplib import FTP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tools"))

from obse_crc import KNOWN, obse_adler  # noqa: E402

TARGET = 0x7934C86C
WORK = os.path.join(HERE, "work")
PATCHED = os.path.join(WORK, "Oblivion.obse.exe")
PATCHER = os.path.join(HERE, "tools", "mk_obse_exe.py")


def die(msg):
    print("\n!! " + msg)
    sys.exit(1)


def has_obse_section(path):
    try:
        import pefile
    except ImportError:
        die("pefile is missing. Run: pip install pefile numpy")
    pe = pefile.PE(path, fast_load=True)
    return any(s.Name.rstrip(b"\0") == b".obse" for s in pe.sections)


def patch(local_exe, out_exe):
    import subprocess
    print("  patching ...")
    r = subprocess.run([sys.executable, PATCHER, local_exe, out_exe, "--target", hex(TARGET)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        die("the patcher failed:\n" + (r.stderr or r.stdout).strip())
    for line in (r.stdout or "").strip().splitlines():
        print("  " + line)


def connect(args):
    ftp = FTP()
    try:
        ftp.connect(args.host, args.port, timeout=120)
        ftp.login()
    except Exception as exc:
        die("cannot reach FTP at %s:%s (%s). Is GoldHEN's FTP server on?" % (args.host, args.port, exc))
    return ftp


def find_game_dir(ftp, args):
    candidates = [
        args.game,
        "/data/PLDN10001/games/22330",
        "/data/playden/games/steam-22330",
    ]
    for cand in candidates:
        try:
            names = [e[0] for e in ftp.mlsd(cand)]
        except Exception:
            continue
        if "Oblivion.exe" in names:
            print("  game folder: " + cand)
            return cand.rstrip("/") + "/"
    die("could not find Oblivion.exe on the console. Check the IP and that the game is installed.")


def ensure_dir(ftp, path):
    try:
        ftp.mkd(path)
        print("  created " + path)
    except Exception:
        pass


def upload(ftp, data, remote):
    ftp.storbinary("STOR " + remote, io.BytesIO(data))
    try:
        ftp.sendcmd("SITE CHMOD 666 " + remote)
    except Exception:
        pass


def sync_manifest(ftp, game, entries):
    buf = io.BytesIO()
    try:
        ftp.retrbinary("RETR " + game + ".playden-tree", buf.write)
    except Exception:
        print("  (no .playden-tree found; Playden will hash the files on its own)")
        return
    lines = []
    for line in buf.getvalue().decode(errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2] in entries:
            sha, size = entries[parts[2]]
            line = "%s\t%d\t%s" % (sha, size, parts[2])
        lines.append(line)
    upload(ftp, ("\n".join(lines) + "\n").encode(), game + ".playden-tree")
    print("  manifest synced")


def install_plugins(ftp, game, obse_dir, northernui_dir):
    if obse_dir:
        src = os.path.join(obse_dir, "obse_1_2_416.dll")
        if not os.path.exists(src):
            die("no obse_1_2_416.dll in " + obse_dir)
        upload(ftp, open(src, "rb").read(), game + "obse_1_2_416.dll")
        print("  installed obse_1_2_416.dll")
        ensure_dir(ftp, game + "Data/OBSE")
        ini = game + "Data/OBSE/obse.ini"
        try:
            ftp.size(ini)
        except Exception:
            cfg = os.path.join(HERE, "config", "obse.ini")
            if os.path.exists(cfg):
                upload(ftp, open(cfg, "rb").read(), ini)
                print("  installed Data/OBSE/obse.ini")
    # OBSE 21.4 reads plugins from Data\OBSE\Plugins only.
    plugins = game + "Data/OBSE/Plugins"
    ensure_dir(ftp, plugins)
    if northernui_dir:
        names = [n for n in sorted(os.listdir(northernui_dir)) if n.lower().startswith("northernui.")]
        if not names:
            die("no NorthernUI.* files in " + northernui_dir)
        for name in names:
            upload(ftp, open(os.path.join(northernui_dir, name), "rb").read(), plugins + "/" + name)
            print("  installed " + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", help="console IP (prompted if omitted)")
    ap.add_argument("--port", type=int, default=2121)
    ap.add_argument("--game", default="/data/PLDN10001/games/22330")
    ap.add_argument("--obse")
    ap.add_argument("--northernui")
    ap.add_argument("--redeploy", action="store_true")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    if not args.host:
        args.host = input("PS4/PS5 IP address (the console running Playden): ").strip()
    if not args.host:
        die("no console IP given")

    os.makedirs(WORK, exist_ok=True)
    ftp = connect(args)
    print("connected to %s:%d" % (args.host, args.port))
    game = find_game_dir(ftp, args)

    if args.redeploy:
        if not os.path.exists(PATCHED):
            die("no saved build at work/Oblivion.obse.exe — run the installer without --redeploy first")
        data = open(PATCHED, "rb").read()
        crc = obse_adler(data)
        if crc != TARGET:
            die("saved build has crc %08X, expected %08X" % (crc, TARGET))
        print("using saved build: %d bytes, crc %08X" % (len(data), crc))
    else:
        print("downloading the game exe Playden runs ...")
        buf = io.BytesIO()
        ftp.retrbinary("RETR " + game + "Oblivion.exe", buf.write)
        console = buf.getvalue()
        local = os.path.join(WORK, "Oblivion.console.exe")
        open(local, "wb").write(console)
        crc = obse_adler(console)
        print("  got %d bytes, crc %08X (%s)" % (len(console), crc, KNOWN.get(crc, "not in OBSE's table")))

        if has_obse_section(local) and crc == TARGET:
            print("  already patched — nothing to rebuild")
            data = console
        else:
            if len(console) > 7_700_000:
                print("  note: this looks like the un-de-stubbed Steam exe; the patcher expects")
                print("        the 7,549,440-byte file Playden runs. Continuing anyway.")
            patch(local, PATCHED)
            data = open(PATCHED, "rb").read()
            if not args.keep:
                os.remove(local)
        if obse_adler(data) != TARGET:
            die("refusing to upload: crc is %08X, OBSE needs %08X" % (obse_adler(data), TARGET))

    # Keep the build on disk: --redeploy re-uploads this after a repair, without
    # touching the console's exe (which Playden may have restored by then).
    open(PATCHED, "wb").write(data)

    sha = hashlib.sha1(data).hexdigest()
    entries = {"Oblivion.exe": (sha, len(data)), "OblivionLauncher.exe": (sha, len(data))}

    print("uploading ...")
    for name in entries:
        upload(ftp, data, game + name)
    print("  Oblivion.exe + OblivionLauncher.exe  sha1 %s" % sha[:16])

    sync_manifest(ftp, game, entries)
    install_plugins(ftp, game, args.obse, args.northernui)

    ok = True
    for name in entries:
        back = io.BytesIO()
        ftp.retrbinary("RETR " + game + name, back.write)
        good = hashlib.sha1(back.getvalue()).hexdigest() == sha
        ok = ok and good
        print("  verified %-22s %s" % (name, "ok" if good else "MISMATCH"))
    ftp.quit()

    if not ok:
        die("a file did not read back correctly; run the installer again")

    print("""
Done.

In Playden: Oblivion > Game settings > Program > Oblivion.exe, then Play.
OBSE loaded correctly when a new obse.log appears in the game folder that ends
with "patched".

If Playden repairs or updates the folder, re-apply everything with:
    python3 install.py --redeploy
""")


if __name__ == "__main__":
    main()
