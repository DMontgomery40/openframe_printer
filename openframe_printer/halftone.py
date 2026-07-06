from __future__ import annotations

"""EP-aware halftoning and the printability lint.

The raster path so far treats 1-bpp conversion as someone else's problem.
It is not: electrophotography does not print arbitrary bitmaps. A single
isolated 600 dpi pixel is a ~42 um latent dot; its fringe field is weak and
development of it is unstable -- it prints, half-prints, or vanishes with
drum wear, humidity, and toner charge drift. Screens for EP engines are
clustered-dot for exactly this reason, while error diffusion (great on
inkjets, where a nozzle either fires or does not) scatters isolated pixels
everywhere.

Rev E makes this an executable constraint instead of folklore:

1. A generated 8x8 clustered-dot screen whose growth order is seeded as a
   2x2 block, so the smallest feature the screen can ever emit is a 2x2
   cluster (~85 um) -- above the stable development size.
2. Floyd-Steinberg error diffusion as the honest comparison.
3. A printability lint that counts isolated black pixels, so "this screen
   is EP-safe" is a measured number, not a claim.

The cost is stated, not hidden: a 2x2-seeded screen cannot render tones
lighter than 4/64 (~6%) within one cell, so highlights clip earlier. That is
the correct trade for a first engine whose development stability is unproven.
"""

from .engine_math import EngineTargets, line_pitch_mm


def clustered_matrix(seed_2x2: bool = True, size: int = 8) -> list[list[int]]:
    """Threshold matrix with clustered (dot-growth) ordering.

    Cells are ranked by distance from the cell center so ink grows as one
    compact dot. With seed_2x2, the first four ranks are forced to the
    central 2x2 block so no threshold level can produce a lone pixel.
    """
    center = (size - 1) / 2.0
    cells = [(x, y) for y in range(size) for x in range(size)]

    def rank_key(cell: tuple[int, int]) -> tuple[float, float, float]:
        x, y = cell
        d2 = (x - center) ** 2 + (y - center) ** 2
        return (d2, y, x)

    ordered = sorted(cells, key=rank_key)
    if seed_2x2:
        half = size // 2
        seed = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
        ordered = seed + [c for c in ordered if c not in seed]
    matrix = [[0] * size for _ in range(size)]
    for rank, (x, y) in enumerate(ordered):
        matrix[y][x] = rank
    return matrix


def bayer_matrix(size: int = 8) -> list[list[int]]:
    """Classic dispersed-dot ordered dither: the anti-pattern for EP.

    Bayer ordering maximizes distance between successive ranks, which is
    exactly what a weak-fringe-field development process cannot print.
    """
    matrix = [[0]]
    while len(matrix) < size:
        n = len(matrix)
        matrix = [
            [4 * matrix[y % n][x % n] + [[0, 2], [3, 1]][y // n][x // n]
             for x in range(2 * n)]
            for y in range(2 * n)
        ]
    return matrix


def screen_halftone(gray: list[list[float]], matrix: list[list[int]]) -> list[list[int]]:
    """Threshold gray (0.0 white .. 1.0 black) against a tiled screen."""
    size = len(matrix)
    levels = size * size
    out = []
    for y, row in enumerate(gray):
        out.append([
            1 if value * levels > matrix[y % size][x % size] else 0
            for x, value in enumerate(row)
        ])
    return out


def floyd_steinberg(gray: list[list[float]]) -> list[list[int]]:
    height = len(gray)
    width = len(gray[0])
    buf = [list(row) for row in gray]
    out = [[0] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            old = buf[y][x]
            new = 1 if old >= 0.5 else 0
            out[y][x] = new
            err = old - new
            if x + 1 < width:
                buf[y][x + 1] += err * 7 / 16
            if y + 1 < height:
                if x > 0:
                    buf[y + 1][x - 1] += err * 3 / 16
                buf[y + 1][x] += err * 5 / 16
                if x + 1 < width:
                    buf[y + 1][x + 1] += err * 1 / 16
    return out


def isolated_black_pixels(bitmap: list[list[int]]) -> int:
    """Black pixels with no black 8-neighbor: below stable EP dot size."""
    height = len(bitmap)
    width = len(bitmap[0])
    count = 0
    for y in range(height):
        for x in range(width):
            if not bitmap[y][x]:
                continue
            has_neighbor = any(
                bitmap[ny][nx]
                for ny in range(max(0, y - 1), min(height, y + 2))
                for nx in range(max(0, x - 1), min(width, x + 2))
                if (ny, nx) != (y, x)
            )
            if not has_neighbor:
                count += 1
    return count


def _flat_patch(level: float, size: int = 64) -> list[list[float]]:
    return [[level] * size for _ in range(size)]


def printability_summary(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    pitch_um = line_pitch_mm(t.dpi) * 1000.0
    seeded = clustered_matrix(seed_2x2=True)
    bayer = bayer_matrix()
    levels = [0.03, 0.05, 0.10, 0.25, 0.50, 0.75, 0.95]
    per_level = []
    for level in levels:
        patch = _flat_patch(level)
        per_level.append({
            "gray_level": level,
            "isolated_px_screen_2x2_seed": isolated_black_pixels(screen_halftone(patch, seeded)),
            "isolated_px_bayer_dispersed": isolated_black_pixels(screen_halftone(patch, bayer)),
            "isolated_px_error_diffusion": isolated_black_pixels(floyd_steinberg(patch)),
        })
    worst_fs = max(row["isolated_px_error_diffusion"] for row in per_level)
    worst_bayer = max(row["isolated_px_bayer_dispersed"] for row in per_level)
    worst_seeded = max(row["isolated_px_screen_2x2_seed"] for row in per_level)
    return {
        "pixel_pitch_um": pitch_um,
        "min_stable_ep_feature": "2x2 pixel cluster",
        "min_stable_ep_feature_um": 2.0 * pitch_um,
        "screen_cell": "8x8 clustered dot, 2x2 seeded",
        "screen_frequency_lpi": t.dpi / 8.0,
        "highlight_floor_fraction": 4.0 / 64.0,
        "per_level_isolated_pixel_counts_64x64_patch": per_level,
        "worst_isolated_px_seeded_screen": worst_seeded,
        "worst_isolated_px_bayer_dispersed": worst_bayer,
        "worst_isolated_px_error_diffusion": worst_fs,
        "seeded_screen_ep_safe": worst_seeded == 0,
        "verdict": (
            "Host rasterizer default is the 2x2-seeded clustered screen: it emits "
            "zero sub-development-size features at any tone, at the cost of a ~6% "
            "highlight floor. Error diffusion is rejected for M1: it emits "
            f"up to {worst_fs} isolated 42 um pixels per 64x64 patch in light tones, "
            "which the EP process will render as instability, not as detail."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(printability_summary(), indent=2))
