from __future__ import annotations

"""Unit-safety layer.

Research Rev B found a 1000x unit error (OPC exposure labeled mJ/cm^2 where
the sources use uJ/cm^2). Rev C makes that *class* of bug mechanically
detectable instead of relying on review luck:

1. Explicit, named conversion functions. Code never multiplies by a bare
   1000 for a unit change; it calls a function whose name states both units.
2. A plausibility table for every unit-suffixed key this package emits.
   `lint_artifact` walks any generated dict and fails loudly when a value
   sits outside the physically plausible window for its unit suffix.

The plausibility windows are deliberately wide. They are not tolerances;
they answer one question: "is this number in the right universe for its
unit?" 0.45 uJ/cm^2 passes; the same figure mislabeled as mJ/cm^2 fails.
"""

MM_PER_INCH = 25.4
KELVIN_OFFSET = 273.15


def mj_cm2_to_uj_cm2(value_mj_cm2: float) -> float:
    return value_mj_cm2 * 1000.0


def uj_cm2_to_mj_cm2(value_uj_cm2: float) -> float:
    return value_uj_cm2 / 1000.0


def mw_cm2_to_uj_cm2_per_us(value_mw_cm2: float) -> float:
    # 1 mW/cm^2 = 1000 uW/cm^2 = 1000 uJ/s/cm^2 = 0.001 uJ/cm^2 per us.
    return value_mw_cm2 * 0.001


def mm_to_um(value_mm: float) -> float:
    return value_mm * 1000.0


def um_to_mm(value_um: float) -> float:
    return value_um / 1000.0


def c_to_k(value_c: float) -> float:
    return value_c + KELVIN_OFFSET


def deg_to_arc_mm(angle_deg: float, diameter_mm: float) -> float:
    import math

    return angle_deg / 360.0 * math.pi * diameter_mm


def arc_mm_to_deg(arc_mm: float, diameter_mm: float) -> float:
    import math

    return arc_mm / (math.pi * diameter_mm) * 360.0


# Plausibility windows keyed by unit suffix. A key matches the LAST suffix in
# this table that it ends with (longest match wins), so `_uj_cm2` keys are not
# caught by a shorter suffix first. Windows are magnitude checks on abs(value).
_UNIT_WINDOWS: list[tuple[str, float, float]] = [
    # suffix, min_abs, max_abs  (0.0 min_abs means zero is allowed)
    ("_uj_cm2", 0.01, 50.0),          # OPC exposure energies live near 0.1-1
    ("_mj_cm2", 0.00001, 0.05),       # if a value is truly mJ/cm^2 it is tiny
    ("_mw_cm2", 0.1, 500.0),          # LED irradiance at the drum
    ("_nm", 200.0, 2000.0),           # optical wavelengths
    ("_um", 0.05, 100000.0),          # micron-scale mechanics
    ("_mm_s", 1.0, 2000.0),           # process speeds
    ("_mm", 0.001, 5000.0),           # printer-scale geometry
    ("_us", 0.001, 1000000.0),        # microsecond timing
    ("_ms", 0.0001, 600000.0),        # millisecond timing
    ("_s", 0.000001, 100000.0),       # second timing
    ("_deg_c", 0.0, 400.0),           # printer temperatures
    ("_c", 0.0, 400.0),
    ("_deg", 0.0, 360.0),             # angles on the drum
    ("_v", 0.0, 10000.0),             # engine voltages incl. transfer HV
    ("_kvpp", 0.1, 10.0),             # AC charging amplitudes
    ("_ua", 0.0, 100000.0),           # HV current limits
    ("_mhz", 0.001, 1000.0),          # shift clocks
    ("_mg_cm2", 0.01, 5.0),           # toner laydown
    ("_gsm", 30.0, 400.0),            # paper weights
    ("_rpm", 0.01, 100000.0),
    ("_kpa", 1.0, 5000.0),            # fuser nip pressures
]

# Keys that intentionally sit outside their suffix window (document why).
_LINT_EXEMPT: set[str] = set()


def _window_for(key: str) -> tuple[float, float] | None:
    best: tuple[str, float, float] | None = None
    lowered = key.lower()
    if "_per_" in lowered:
        # Composite rate units (e.g. heat_capacity_j_per_c, ramp_v_per_s)
        # are not simple unit-suffixed values; the suffix is a denominator.
        return None
    for suffix, lo, hi in _UNIT_WINDOWS:
        if lowered.endswith(suffix):
            if best is None or len(suffix) > len(best[0]):
                best = (suffix, lo, hi)
    if best is None:
        return None
    return best[1], best[2]


def lint_artifact(data: object, path: str = "") -> list[str]:
    """Return a list of unit-plausibility violations found in a generated artifact.

    Walks dicts/lists; checks numeric leaves whose key carries a known unit
    suffix. An empty return means every unit-suffixed number is in the right
    universe for its unit -- nothing more.
    """
    problems: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else str(key)
            if isinstance(value, (dict, list)):
                problems.extend(lint_artifact(value, child_path))
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            if child_path in _LINT_EXEMPT:
                continue
            window = _window_for(str(key))
            if window is None:
                continue
            lo, hi = window
            magnitude = abs(float(value))
            if magnitude == 0.0:
                # Zero is never a unit-magnitude error: scaling zero by any
                # wrong factor is still zero.
                continue
            if not (lo <= magnitude <= hi):
                problems.append(
                    f"{child_path} = {value} outside plausibility window "
                    f"[{lo}, {hi}] for its unit suffix"
                )
    elif isinstance(data, list):
        for index, item in enumerate(data):
            problems.extend(lint_artifact(item, f"{path}[{index}]"))
    return problems
