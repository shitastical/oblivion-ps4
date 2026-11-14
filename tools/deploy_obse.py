#!/usr/bin/env python3
"""Push the patched Oblivion.exe to the console and keep Playden's verify happy.

Playden hashes the bottle's files (.playden-tree: sha1, size, name) on every
Play and "repairs" anything that does not match. A patched exe would therefore be
reverted. This rewrites the manifest entries after uploading, so verify finds
nothing to restore.

The launcher name is uploaded with the same bytes: Playden's recipe can start
either name, and both must reach the self-loading exe (the stock obse_loader.exe
is what fails with error 50).

Usage:
    python3 deploy_obse.py <patched.exe> [--host CONSOLE_IP] [--port 2121]
                           [--game /data/PLDN10001/games/22330] [--target 7934C86C]
"""
import argparse
import hashlib
import io
import sys
from ftplib import FTP

P = 65521


def obse_adler(data):
    buf = bytearray(data)
    if len(buf) > 0x13E:
        buf[0x13E] &= ~0x20
    a, b = 1, 0
    for x in buf:
        a = (a + x) % P
        b = (b + a) % P
    return (b << 16) | a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--host", help="console IP (prompted if omitted)")
    ap.add_argument("--port", type=int, default=2121)
    ap.add_argument("--game", default="/data/PLDN10001/games/22330")
    ap.add_argument("--target", default="7934C86C")
    args = ap.parse_args()

    if not args.host:
        args.host = input("PS4/PS5 IP address: ").strip()

    data = open(args.exe, "rb").read()
    target = int(args.target, 0)
    crc = obse_adler(data)
    if crc != target:
        sys.exit("%s has crc %08X, OBSE expects %08X" % (args.exe, crc, target))
    sha = hashlib.sha1(data).hexdigest()
    print("%s  %d bytes  crc %08X  sha1 %s" % (args.exe, len(data), crc, sha))

    game = args.game.rstrip("/") + "/"
    ftp = FTP()
    ftp.connect(args.host, args.port, timeout=120)
    ftp.login()
    for name in ("Oblivion.exe", "OblivionLauncher.exe"):
        ftp.storbinary("STOR " + game + name, io.BytesIO(data))
        ftp.sendcmd("SITE CHMOD 666 " + game + name)

    entries = {n: (sha, len(data)) for n in ("Oblivion.exe", "OblivionLauncher.exe")}
    buf = io.BytesIO()
    ftp.retrbinary("RETR " + game + ".playden-tree", buf.write)
    lines = []
    for line in buf.getvalue().decode().splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2] in entries:
            new_sha, size = entries[parts[2]]
            line = "%s\t%d\t%s" % (new_sha, size, parts[2])
        lines.append(line)
    ftp.storbinary("STOR " + game + ".playden-tree", io.BytesIO(("\n".join(lines) + "\n").encode()))

    ok = True
    for name in entries:
        back = io.BytesIO()
        ftp.retrbinary("RETR " + game + name, back.write)
        got = back.getvalue()
        good = hashlib.sha1(got).hexdigest() == sha and len(got) == len(data)
        ok = ok and good
        print("  %-22s %s" % (name, "ok" if good else "MISMATCH"))
    ftp.quit()
    print("manifest synced" if ok else "UPLOAD FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
