from __future__ import annotations

"""EP-aware halftoning and the printability lint.

Rev E correctly rejected dispersed-dot screens for the first OpenFrame EP
engine, but it left a bug in the exact place it claimed to have made
executable: a continuous threshold against a 2x2-seeded clustered screen can
still emit one central pixel for tones below 1/64. That single pixel is exactly
the unstable 42 µm feature the screen was supposed to forbid.

Rev F keeps the raw threshold function for comparison, then adds a production
screen that enforces the physical floor:

1. no requested local tone below the 2x2 seed threshold is allowed to emit a
   partial seed;
2. a post-screen feature lint removes any connected black component that is
   smaller than the required seed or lacks a 2x2 nucleus;
3. generated artifacts report the tone-floor cost instead of hiding it.

The design choice is intentionally conservative: highlights below 4/64 are
clipped to paper white until the H1/PIDC rig proves that smaller developed
features survive on the selected OPC/toner/developer stack.
"""

from collections import deque
from copy import deepcopy

from .engine_math import EngineTargets, line_pitch_mm

EP_MIN_CLUSTER_PIXELS = 4


def clustered_matrix(seed_2x2: bool = True, size: int = 8) -> list[list[int]]:
    """Threshold matrix with clustered (dot-growth) ordering.

    Cells are ranked by distance from the cell center so ink grows as one
    compact dot. With seed_2x2, the first four ranks are forced to the
    central 2x2 block. Rev F's production screen additionally clips partial
    seeds below rank 4; the raw matrix alone is not enough.
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
    """Classic dispersed-dot ordered dither: the anti-pattern for M1 EP."""
    matrix = [[0]]
    while len(matrix) < size:
        n = len(matrix)
        matrix = [
            [
                4 * matrix[y % n][x % n] + [[0, 2], [3, 1]][y // n][x // n]
                for x in range(2 * n)
            ]
            for y in range(2 * n)
        ]
    return matrix


def screen_halftone(gray: list[list[float]], matrix: list[list[int]]) -> list[list[int]]:
    """Raw threshold gray (0.0 white .. 1.0 black) against a tiled screen.

    This is retained for tests and comparisons. It is not the M1 production
    screen because it can emit a partial 2x2 seed at sub-floor highlight tones.
    """
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


def _neighbors8(x: int, y: int, width: int, height: int):
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if (nx, ny) != (x, y):
                yield nx, ny


def isolated_black_pixels(bitmap: list[list[int]]) -> int:
    """Black pixels with no black 8-neighbor: below stable EP dot size."""
    height = len(bitmap)
    width = len(bitmap[0])
    count = 0
    for y in range(height):
        for x in range(width):
            if not bitmap[y][x]:
                continue
            has_neighbor = any(bitmap[ny][nx] for nx, ny in _neighbors8(x, y, width, height))
            if not has_neighbor:
                count += 1
    return count


def _black_components(bitmap: list[list[int]]) -> list[list[tuple[int, int]]]:
    height = len(bitmap)
    width = len(bitmap[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for y in range(height):
        for x in range(width):
            if not bitmap[y][x] or (x, y) in seen:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen.add((x, y))
            comp: list[tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                comp.append((cx, cy))
                for nx, ny in _neighbors8(cx, cy, width, height):
                    if bitmap[ny][nx] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        q.append((nx, ny))
            components.append(comp)
    return components


def _component_has_2x2(bitmap: list[list[int]], comp: list[tuple[int, int]]) -> bool:
    pixels = set(comp)
    for x, y in pixels:
        if {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)} <= pixels:
            return True
    return False


def feature_metrics(bitmap: list[list[int]], min_cluster_pixels: int = EP_MIN_CLUSTER_PIXELS) -> dict:
    """Return EP printability metrics for a binary bitmap."""
    components = _black_components(bitmap)
    subclusters = [
        comp for comp in components
        if len(comp) < min_cluster_pixels or not _component_has_2x2(bitmap, comp)
    ]
    black = sum(sum(row) for row in bitmap)
    return {
        "black_pixels": black,
        "black_components": len(components),
        "isolated_black_pixels": isolated_black_pixels(bitmap),
        "sub_min_cluster_components": len(subclusters),
        "sub_min_cluster_pixels": sum(len(comp) for comp in subclusters),
        "smallest_component_pixels": min((len(comp) for comp in components), default=0),
        "all_components_have_2x2_nucleus": all(_component_has_2x2(bitmap, comp) for comp in components) if components else True,
        "ep_safe": len(subclusters) == 0,
    }


def suppress_subclusters(bitmap: list[list[int]], min_cluster_pixels: int = EP_MIN_CLUSTER_PIXELS) -> list[list[int]]:
    """Remove connected black features smaller than the EP seed requirement."""
    out = deepcopy(bitmap)
    for comp in _black_components(bitmap):
        if len(comp) < min_cluster_pixels or not _component_has_2x2(bitmap, comp):
            for x, y in comp:
                out[y][x] = 0
    return out


def ep_safe_clustered_halftone(
    gray: list[list[float]],
    matrix: list[list[int]] | None = None,
    min_cluster_pixels: int = EP_MIN_CLUSTER_PIXELS,
) -> list[list[int]]:
    """Production M1 screen: clustered threshold plus a physical feature floor.

    The local floor prevents partial-seed output on flat highlight patches; the
    component suppressor catches pathological image edges or host-generated
    rasters that would otherwise form a sub-2x2 feature.
    """
    m = matrix or clustered_matrix(seed_2x2=True)
    size = len(m)
    levels = size * size
    floor = min_cluster_pixels / levels
    raw = []
    for y, row in enumerate(gray):
        raw.append([
            1 if value >= floor and value * levels > m[y % size][x % size] else 0
            for x, value in enumerate(row)
        ])
    return suppress_subclusters(raw, min_cluster_pixels=min_cluster_pixels)


def _flat_patch(level: float, size: int = 64) -> list[list[float]]:
    return [[level] * size for _ in range(size)]


def halftone_floor_gate(target: EngineTargets | None = None) -> dict:
    """Executable Rev F gate proving the Rev E sub-floor bug and the Rev F fix."""
    t = target or EngineTargets()
    seeded = clustered_matrix(seed_2x2=True)
    levels = [0.001, 0.005, 0.010, 1.0 / 64.0, 0.020, 0.030, 0.050, 4.0 / 64.0]
    rows = []
    for level in levels:
        raw = screen_halftone(_flat_patch(level, 64), seeded)
        safe = ep_safe_clustered_halftone(_flat_patch(level, 64), seeded)
        rows.append({
            "gray_level": level,
            "raw_seeded_black_pixels": feature_metrics(raw)["black_pixels"],
            "raw_seeded_isolated_pixels": feature_metrics(raw)["isolated_black_pixels"],
            "raw_seeded_sub_min_cluster_components": feature_metrics(raw)["sub_min_cluster_components"],
            "revF_safe_black_pixels": feature_metrics(safe)["black_pixels"],
            "revF_safe_isolated_pixels": feature_metrics(safe)["isolated_black_pixels"],
            "revF_safe_sub_min_cluster_components": feature_metrics(safe)["sub_min_cluster_components"],
        })
    return {
        "revision": "M1-REV-F",
        "finding": (
            "Rev E's raw 2x2-seeded screen still emits partial seeds below the 4/64 tone floor; "
            "the production screen must clip or suppress those features."
        ),
        "pixel_pitch_um": line_pitch_mm(t.dpi) * 1000.0,
        "physical_min_cluster_pixels": EP_MIN_CLUSTER_PIXELS,
        "physical_min_cluster_um": 2.0 * line_pitch_mm(t.dpi) * 1000.0,
        "declared_highlight_floor_fraction": EP_MIN_CLUSTER_PIXELS / 64.0,
        "per_level_floor_check_64x64_patch": rows,
        "revE_raw_screen_bug_reproduced": any(
            row["raw_seeded_isolated_pixels"] > 0 or row["raw_seeded_sub_min_cluster_components"] > 0
            for row in rows
        ),
        "revF_screen_passes_floor_gate": all(
            row["revF_safe_isolated_pixels"] == 0 and row["revF_safe_sub_min_cluster_components"] == 0
            for row in rows
        ),
    }


def printability_summary(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    pitch_um = line_pitch_mm(t.dpi) * 1000.0
    seeded = clustered_matrix(seed_2x2=True)
    bayer = bayer_matrix()
    levels = [0.001, 0.005, 0.010, 1.0 / 64.0, 0.03, 0.05, 0.10, 0.25, 0.50, 0.75, 0.95]
    per_level = []
    for level in levels:
        patch = _flat_patch(level)
        raw_screen = screen_halftone(patch, seeded)
        safe_screen = ep_safe_clustered_halftone(patch, seeded)
        bayer_out = screen_halftone(patch, bayer)
        fs_out = floyd_steinberg(patch)
        per_level.append({
            "gray_level": level,
            "raw_seeded_metrics": feature_metrics(raw_screen),
            "revF_safe_seeded_metrics": feature_metrics(safe_screen),
            "bayer_dispersed_metrics": feature_metrics(bayer_out),
            "error_diffusion_metrics": feature_metrics(fs_out),
        })
    worst_fs = max(row["error_diffusion_metrics"]["isolated_black_pixels"] for row in per_level)
    worst_bayer = max(row["bayer_dispersed_metrics"]["isolated_black_pixels"] for row in per_level)
    worst_seeded = max(row["revF_safe_seeded_metrics"]["isolated_black_pixels"] for row in per_level)
    worst_subcluster_safe = max(row["revF_safe_seeded_metrics"]["sub_min_cluster_components"] for row in per_level)
    raw_bug = halftone_floor_gate(t)
    return {
        "revision": "M1-REV-F",
        "pixel_pitch_um": pitch_um,
        "min_stable_ep_feature": "2x2 pixel cluster",
        "min_stable_ep_feature_um": 2.0 * pitch_um,
        "screen_cell": "8x8 clustered dot, 2x2 seed, Rev F subcluster suppression",
        "screen_frequency_lpi": t.dpi / 8.0,
        "highlight_floor_fraction": EP_MIN_CLUSTER_PIXELS / 64.0,
        "revE_floor_bug_reproduced": raw_bug["revE_raw_screen_bug_reproduced"],
        "per_level_feature_metrics_64x64_patch": per_level,
        "worst_isolated_px_revF_seeded_screen": worst_seeded,
        "worst_isolated_px_seeded_screen": worst_seeded,  # compatibility alias, now Rev F-safe screen
        "worst_sub_min_cluster_components_revF_seeded_screen": worst_subcluster_safe,
        "worst_isolated_px_bayer_dispersed": worst_bayer,
        "worst_isolated_px_error_diffusion": worst_fs,
        "seeded_screen_ep_safe": worst_seeded == 0 and worst_subcluster_safe == 0,
        "verdict": (
            "Host rasterizer default is the Rev F 2x2-seeded clustered screen with a real "
            "subcluster floor: it emits zero isolated or sub-2x2 developed features at every "
            "tested tone, at the cost of clipping highlights below 4/64. Error diffusion is "
            f"rejected for M1: it emits up to {worst_fs} isolated 42 um pixels per 64x64 patch."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(printability_summary(), indent=2))
