"""A made-up drawing shaped like an IWMAC panel in VectorCraft, to time drags without any plant's data.

    python3 build/bench-drawing.py > bench.svg

1400 x 750 px, about 660 elements, like a Maskin panel opened by the userscript:
- a ground;
- 26 pipes;
- 40 shapes;
- 140 object placeholders: a small PNG picture, an opaque dashed box, and every other one a caption;
- 49 pills under them.

Drop it on the editor, select the small red square at the bottom right and drag it. VectorCraft's status bar shows
`render N ms` for each frame. Compare the build you are trying with the live one, in the same window size.
"""
import base64
import random
import struct
import sys
import zlib

random.seed(7)


def png(w, h, pixel):
    """A small RGBA PNG; pixel(x, y) -> (r, g, b, a)."""
    raw = b"".join(b"\x00" + b"".join(struct.pack("4B", *pixel(x, y)) for x in range(w)) for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def pill(x, y, w=40, h=20):
    """A white pill with a grey ring and some dark 'digits', as a value's picture."""
    r = h / 2
    dx = max(0.0, abs(x + 0.5 - w / 2) - (w / 2 - r))
    d = (dx * dx + (y + 0.5 - h / 2) ** 2) ** 0.5
    if d > r:
        return (0, 0, 0, 0)
    if d > r - 1.5:
        return (106, 125, 136, 255)
    if 6 < y < 14 and 8 < x < 32 and (x // 3) % 2 == 0:
        return (40, 50, 60, 255)
    return (255, 255, 255, 255)


look = "data:image/png;base64," + base64.b64encode(png(40, 20, pill)).decode()
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="750" viewBox="0 0 1400 750">',
       '<g id="Bakgrunn" data-name="Bakgrunn"><rect width="1400" height="750" fill="#cccccc"/></g>',
       '<g id="Ror" data-name="Rør">']
for i in range(26):
    x0, y0 = random.randint(40, 1100), random.randint(40, 700)
    x1, y1 = random.randint(40, 1100), random.randint(40, 700)
    out.append(f'<path d="M{x0} {y0} H{x1} V{y1}" fill="none" stroke="#83c2ce" stroke-width="2"/>')
out.append('</g><g id="Former" data-name="Former">')
for i in range(40):
    x, y = random.randint(40, 1050), random.randint(40, 680)
    out.append(f'<path d="M{x} {y} h60 a8 8 0 0 1 8 8 v24 a8 8 0 0 1 -8 8 h-60 a8 8 0 0 1 -8 -8 v-24 a8 8 0 0 1 8 -8 Z" '
               'fill="#ffffff" stroke="#9ea5af" stroke-width="2"/>')
out.append('</g><g id="IWMAC-objekter" data-name="IWMAC-objekter">')
for i in range(49):
    x, y = 40 + (i % 7) * 150, 60 + (i // 7) * 95
    out.append(f'<g data-name="Ramme"><rect x="{x}" y="{y}" width="39" height="19" rx="9.5" ry="9.5" fill="#ffffff" '
               'stroke="#6a7d88" stroke-width="1.25"/></g>')
for i in range(140):
    x, y = 30 + (i % 14) * 80, 40 + (i // 14) * 70
    parts = [f'<image x="0" y="0" width="40" height="20" preserveAspectRatio="xMidYMid meet" href="{look}"/>',
             '<path d="M0 0 L40 0 L40 20 L0 20 Z" fill="none" stroke="#819eeb" stroke-width="1" stroke-dasharray="3 2"/>']
    if i % 2 == 0:
        parts.append('<text x="0" y="31" font-family="Source Sans 3" font-size="9" fill="#3c4650">Value %d</text>' % i)
    out.append(f'<g id="obj_{i}" data-name="IWMAC object {i}" transform="translate({x} {y})">' + "".join(parts) + "</g>")
out.append('</g><g id="Bench" data-name="Bench"><rect x="1300" y="690" width="30" height="20" fill="#ff0000"/></g></svg>')
sys.stdout.write("\n".join(out) + "\n")
