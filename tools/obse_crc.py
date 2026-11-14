"""OBSE's checksum: clear the large-address-aware bit at file offset 0x13E, then
Adler32 the whole file. This is the number OBSE prints as "crc = ..." and the
only thing it uses to decide whether the exe is a version it supports."""

P = 65521

KNOWN = {
    0x7934C86C: "retail 1.2.0.416 (obse_1_2_416.dll, no steam flag)",
    0xA2408F04: "retail 1.2.0.416 steam build (obse_1_2_416.dll, steam flag)",
}


def obse_adler(data):
    buf = bytearray(data)
    if len(buf) > 0x13E:
        buf[0x13E] &= ~0x20
    a, b = 1, 0
    for x in buf:
        a = (a + x) % P
        b = (b + a) % P
    return (b << 16) | a
