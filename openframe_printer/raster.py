from __future__ import annotations

from pathlib import Path

FONT = {
    " ": ["00000","00000","00000","00000","00000","00000","00000"],
    "-": ["00000","00000","00000","11111","00000","00000","00000"],
    ".": ["00000","00000","00000","00000","00000","01100","01100"],
    ":": ["00000","01100","01100","00000","01100","01100","00000"],
}

def _glyph(ch: str) -> list[str]:
    ch = ch.upper()
    if ch in FONT:
        return FONT[ch]
    # Tiny fallback: deterministic blocky pseudo-glyph based on character code.
    code = ord(ch)
    rows = []
    for y in range(7):
        row = ""
        for x in range(5):
            bit = ((code >> ((x + y) % 7)) ^ (x * 3 + y)) & 1
            border = x in (0, 4) or y in (0, 6)
            row += "1" if bit and not (ch.islower()) or (border and ch.isalnum()) else "0"
        rows.append(row)
    return rows


def text_to_bitmap(text: str, scale: int = 3, margin: int = 24) -> list[list[int]]:
    lines = text.splitlines() or [""]
    char_w = 6 * scale
    char_h = 8 * scale
    width = max(1, max(len(line) for line in lines) * char_w + margin * 2)
    height = max(1, len(lines) * char_h + margin * 2)
    bmp = [[0 for _ in range(width)] for _ in range(height)]
    for line_i, line in enumerate(lines):
        y0 = margin + line_i * char_h
        for col, ch in enumerate(line):
            glyph = _glyph(ch)
            x0 = margin + col * char_w
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                yy = y0 + gy * scale + sy
                                xx = x0 + gx * scale + sx
                                if 0 <= yy < height and 0 <= xx < width:
                                    bmp[yy][xx] = 1
    return bmp


def write_pbm(bitmap: list[list[int]], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    h = len(bitmap)
    w = len(bitmap[0]) if h else 0
    with p.open("w", encoding="ascii") as f:
        f.write(f"P1\n{w} {h}\n")
        for row in bitmap:
            f.write(" ".join("1" if px else "0" for px in row) + "\n")
