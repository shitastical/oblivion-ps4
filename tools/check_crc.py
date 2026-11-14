#!/usr/bin/env python3
"""Print the value OBSE reports as "crc = ..." for one or more exes.

OBSE's supported builds are listed in its version table by this number. If a file
prints anything OBSE does not know, the loader says "You have an unknown version
of Oblivion" and refuses to start the game.

Usage: python3 check_crc.py Oblivion.exe [...]
"""
import sys

P = 65521


def obse_adler(data):
    buf = bytearray(data)
    if len(buf) > 0x13E:
        buf[0x13E] &= ~0x20  # OBSE clears the large-address-aware bit first
    a, b = 1, 0
    for x in buf:
        a = (a + x) % P
        b = (b + a) % P
    return (b << 16) | a


KNOWN = {
    0x7934C86C: "retail 1.2.0.416 (obse_1_2_416.dll, no steam flag)",
    0xA2408F04: "retail 1.2.0.416 steam build (obse_1_2_416.dll, steam flag)",
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        crc = obse_adler(open(path, "rb").read())
        print("%-40s crc = %08X  %s" % (path, crc, KNOWN.get(crc, "NOT in OBSE's table")))
