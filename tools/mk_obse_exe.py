#!/usr/bin/env python3
"""Make Oblivion.exe load OBSE itself, so obse_loader.exe is never needed.

Why: on Playden (PS4/PS5) obse_loader.exe fails with
    Assertion failed in main.cpp (129): Launching Oblivion failed (code = 00000032 (50))
because the runtime refuses the suspended CreateProcess the loader uses. This
script instead appends an ".obse" section whose stub runs before the game's real
entry point:

    pushad / push "obse_1_2_416.dll" / call [LoadLibraryA] / popad / jmp entry

It then forces the file's Adler32 (the value OBSE prints as "crc =") to the one
OBSE accepts for this build, by solving for an overlay of appended bytes.

Usage:
    python3 mk_obse_exe.py <source.exe> <output.exe> [--dll obse_1_2_416.dll]
                           [--target 7934C86C]

<source.exe> must be the *de-stubbed* Oblivion.exe that Playden runs (7,549,440
bytes, entry point 0x58787C). Do not use the Steam-downloaded 7,898,624-byte
file: it still carries the Steam stub and its .bind section.

Requires: pip install pefile numpy
"""
import argparse
import hashlib
import struct

import pefile

P = 65521
DEFAULT_DLL = "obse_1_2_416.dll"
DEFAULT_TARGET = 0x7934C86C  # retail Oblivion 1.2.0.416, no steam flag


def align(value, boundary):
    return (value + boundary - 1) // boundary * boundary


def obse_adler(data):
    """OBSE's TestChecksum: clear the LAA bit at 0x13E, then Adler32 the file."""
    buf = bytearray(data)
    if len(buf) > 0x13E:
        buf[0x13E] &= ~0x20
    a, b = 1, 0
    for x in buf:
        a = (a + x) % P
        b = (b + a) % P
    return (b << 16) | a


def force_adler(data, target):
    """Append an overlay so obse_adler(data + overlay) == target."""
    import numpy as np

    buf = bytearray(data)
    if len(buf) > 0x13E:
        buf[0x13E] &= ~0x20
    a0, b0 = 1, 0
    for x in buf:
        a0 = (a0 + x) % P
        b0 = (b0 + a0) % P

    ar, br = np.arange(256, dtype=np.int64), np.arange(256, dtype=np.int64)
    want_a, want_b = target & 0xFFFF, (target >> 16) & 0xFFFF

    for total in range(300, 1000, 3):            # sum of the four overlay bytes
        need = (want_a - total - a0) % P          # pre-pad that lands a on want_a
        q, r = divmod(need, 255)
        prepad = bytearray([255] * q + ([r] if r else []))
        prepad += bytes(260 - len(prepad))
        base = bytes(buf) + bytes(prepad)
        pa, pb = a0, b0
        for x in prepad:
            pa = (pa + x) % P
            pb = (pb + pa) % P
        for length in range(260, 700):
            # b grows by length*pa plus sum((length-i)*y_i)
            want = (want_b - pb - length * pa) % P
            w1, w2, w3, w4 = length, length - 1, length - 2, length - 3
            s2 = (total - ar[:, None] - br[None, :]) % P
            k2 = (want - w1 * ar[:, None] - w2 * br[None, :]) % P
            c = (k2 - w4 * s2) % P
            d = (s2 - c) % P
            hit = np.argwhere((c <= 255) & (d <= 255))
            if len(hit):
                i, j = hit[0]
                overlay = bytearray(length)
                overlay[0], overlay[1] = int(i), int(j)
                overlay[2], overlay[3] = int(c[i, j]), int(d[i, j])
                out = base + bytes(overlay)
                if obse_adler(out) == target:
                    return out
    raise SystemExit("could not force the checksum; pass --target with a value OBSE supports")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("output")
    ap.add_argument("--dll", default=DEFAULT_DLL)
    ap.add_argument("--target", default=hex(DEFAULT_TARGET))
    args = ap.parse_args()
    target = int(args.target, 0)

    pe = pefile.PE(args.source)

    # LoadLibraryA's IAT slot. pefile's ImportData.address is unreliable on the
    # de-stubbed exe, so use FirstThunk + 4 * index (verified: resolves to the
    # hint/name entry for LoadLibraryA).
    iat = None
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        if entry.dll.decode().upper().startswith("KERNEL32"):
            for index, imp in enumerate(entry.imports):
                if imp.name and imp.name.decode() == "LoadLibraryA":
                    iat = pe.OPTIONAL_HEADER.ImageBase + entry.struct.FirstThunk + 4 * index
    if iat is None:
        raise SystemExit("LoadLibraryA is not imported by this exe")

    image_base = pe.OPTIONAL_HEADER.ImageBase
    last = pe.sections[-1]
    new_rva = align(last.VirtualAddress + last.Misc_VirtualSize, pe.OPTIONAL_HEADER.SectionAlignment)
    raw_end = last.PointerToRawData + last.SizeOfRawData
    data = bytearray(open(args.source, "rb").read())
    if len(data) != raw_end:
        raise SystemExit("unexpected layout: file size does not end with the last section")

    entry = image_base + pe.OPTIONAL_HEADER.AddressOfEntryPoint
    va = image_base + new_rva
    stub = bytearray()
    stub += b"\x60"                                # pushad
    stub += b"\x68\x00\x00\x00\x00"                # push <dll name>
    stub += b"\xff\x15" + struct.pack("<I", iat)   # call [LoadLibraryA]
    stub += b"\x61"                                # popad
    stub += b"\xe9\x00\x00\x00\x00"                # jmp original entry
    while len(stub) < align(len(stub), 16):
        stub += b"\x90"
    str_off = len(stub)
    struct.pack_into("<I", stub, 2, va + str_off)
    struct.pack_into("<i", stub, 14, entry - (va + 13 + 5))
    stub += args.dll.encode() + b"\x00"
    size_raw = align(len(stub), pe.OPTIONAL_HEADER.FileAlignment)

    header_off = last.get_file_offset() + 40
    if header_off + 40 > pe.OPTIONAL_HEADER.SizeOfHeaders:
        raise SystemExit("no room for another section header")
    data[header_off:header_off + 40] = struct.pack(
        "<8sIIIIIIHHI", b".obse", len(stub), new_rva, size_raw, raw_end, 0, 0, 0, 0, 0x60000020)
    struct.pack_into("<H", data, pe.DOS_HEADER.e_lfanew + 6, pe.FILE_HEADER.NumberOfSections + 1)
    opt = pe.OPTIONAL_HEADER.get_file_offset()
    struct.pack_into("<I", data, opt + 16, new_rva)  # AddressOfEntryPoint
    struct.pack_into("<I", data, opt + 56, align(new_rva + len(stub), pe.OPTIONAL_HEADER.SectionAlignment))
    data += bytes(size_raw - len(stub))
    data[raw_end:raw_end + len(stub)] = stub

    final = force_adler(bytes(data), target)
    open(args.output, "wb").write(final)
    crc = obse_adler(final)
    print("entry %08x -> .obse at %08x, calls LoadLibraryA via %08x" % (entry, new_rva, iat))
    print("%s: %d bytes, crc = %08X (%s)" % (args.output, len(final), crc, "ok" if crc == target else "FAIL"))
    print("sha1 %s" % hashlib.sha1(final).hexdigest())


if __name__ == "__main__":
    main()
