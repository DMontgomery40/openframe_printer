from __future__ import annotations

"""Rev G OFP1 real-time spool and buffer budget.

Rev E correctly defined OFP1 framing and proved the byte stream is reliable.
It did not prove that a tiny MCU can feed a moving electrophotographic engine
from USB Full Speed without underrun. Bulk USB is a best-effort pipe; the page
engine is not best-effort once the clutch starts.

This module turns that distinction into numbers: decoded line-buffer drain,
host-delivery surplus, pause tolerance, and RP2040-class SRAM feasibility. The
model is intentionally conservative and deterministic; it is a build gate, not
a statistical USB benchmark.
"""

from dataclasses import dataclass, asdict
import math

from .engine_math import EngineTargets, line_rate_lps, lines_down, page_bytes
from .ofp1 import FRAME_OVERHEAD_BYTES, transport_budget

USB_FS_BULK_CEILING_BYTES_PER_S = 19 * 64 * 1000  # theoretical best case: 1216 B/ms
USB_HS_BULK_NOMINAL_BYTES_PER_S = 30_000_000      # deliberately below the theoretical bus maximum
RP2040_SRAM_BYTES = 264 * 1024


@dataclass(frozen=True)
class SpoolCase:
    name: str
    host_bus: str
    host_bytes_per_s: float
    ring_buffer_bytes: int
    start_prefill_bytes: int
    host_pause_ms: float
    ppm: float


def _line_drain_bytes_per_s(target: EngineTargets, ppm: float | None = None) -> float:
    if ppm is None or ppm == target.ppm:
        rate = line_rate_lps(target)
    else:
        scaled = EngineTargets(**{**target.__dict__, "ppm": int(round(ppm))})
        # preserve fractional ppm exactly rather than dataclass int coercion assumptions
        rate = line_rate_lps(target) * ppm / target.ppm
    return page_bytes(target.led_pixels, 1) * rate


def _page_duration_s(target: EngineTargets, ppm: float | None = None) -> float:
    return 60.0 / (target.ppm if ppm is None else ppm)


def _solid_page_payload_bytes(target: EngineTargets) -> int:
    return page_bytes(target.led_pixels, lines_down(target.letter_length_mm, target.dpi))


def evaluate_spool_case(case: SpoolCase, target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    drain = _line_drain_bytes_per_s(t, case.ppm)
    page_s = _page_duration_s(t, case.ppm)
    pause_drain = drain * case.host_pause_ms / 1000.0
    usable_prefill = min(case.start_prefill_bytes, case.ring_buffer_bytes)
    survives_pause = usable_prefill >= pause_drain
    surplus = case.host_bytes_per_s - drain
    if surplus <= 0.0:
        refill_s = math.inf
    else:
        refill_s = max(0.0, pause_drain - usable_prefill) / surplus
    can_finish_streaming = case.host_bytes_per_s >= drain and survives_pause
    return {
        "case": case.name,
        "host_bus": case.host_bus,
        "host_bytes_per_s": case.host_bytes_per_s,
        "ppm": case.ppm,
        "line_drain_bytes_per_s": drain,
        "line_drain_mbit_s": drain * 8.0 / 1_000_000.0,
        "page_duration_s": page_s,
        "ring_buffer_bytes": case.ring_buffer_bytes,
        "ring_buffer_lines": case.ring_buffer_bytes / page_bytes(t.led_pixels, 1),
        "start_prefill_bytes": case.start_prefill_bytes,
        "host_pause_ms": case.host_pause_ms,
        "bytes_drained_during_pause": pause_drain,
        "pause_tolerance_ms_at_prefill": usable_prefill / drain * 1000.0,
        "survives_pause": survives_pause,
        "host_surplus_bytes_per_s": surplus,
        "refill_seconds_after_pause": None if math.isinf(refill_s) else refill_s,
        "can_finish_streaming_without_underrun": can_finish_streaming,
    }


def max_ppm_for_host_utilization(
    target: EngineTargets | None = None,
    host_bytes_per_s: float = USB_FS_BULK_CEILING_BYTES_PER_S,
    max_utilization: float = 0.60,
) -> float:
    t = target or EngineTargets()
    drain_at_target = _line_drain_bytes_per_s(t)
    return t.ppm * (host_bytes_per_s * max_utilization) / drain_at_target


def realtime_spool_summary(target: EngineTargets | None = None) -> dict:
    t = target or EngineTargets()
    base = transport_budget(t)
    row_bytes = page_bytes(t.led_pixels, 1)
    line_rate = line_rate_lps(t)
    drain = row_bytes * line_rate
    required_100ms = math.ceil(drain * 0.100)
    rev_e_ring = int(base["recommended_engine_ring_buffer_bytes"])
    rp2040_practical_ring = 128 * 1024
    external_page_ram = 8 * 1024 * 1024
    solid_page_payload = _solid_page_payload_bytes(t)
    solid_page_on_wire = int(base["solid_letter_page_bytes_on_wire"])

    cases = [
        SpoolCase(
            "revE_32_line_ring_10ms_target_only",
            "USB_FS",
            USB_FS_BULK_CEILING_BYTES_PER_S * 0.80,
            rev_e_ring,
            rev_e_ring,
            100.0,
            float(t.ppm),
        ),
        SpoolCase(
            "rp2040_128KiB_ring_fs_80pct_with_100ms_pause",
            "USB_FS",
            USB_FS_BULK_CEILING_BYTES_PER_S * 0.80,
            rp2040_practical_ring,
            required_100ms,
            100.0,
            float(t.ppm),
        ),
        SpoolCase(
            "usb_fs_75pct_worst_case_12ppm_no_margin",
            "USB_FS",
            USB_FS_BULK_CEILING_BYTES_PER_S * 0.75,
            rp2040_practical_ring,
            required_100ms,
            100.0,
            float(t.ppm),
        ),
        SpoolCase(
            "usb_fs_degraded_8ppm_old_32_line_ring_still_fails_100ms",
            "USB_FS",
            USB_FS_BULK_CEILING_BYTES_PER_S * 0.75,
            rev_e_ring,
            rev_e_ring,
            100.0,
            8.0,
        ),
        SpoolCase(
            "usb_fs_degraded_8ppm_128KiB_ring_passes_100ms",
            "USB_FS",
            USB_FS_BULK_CEILING_BYTES_PER_S * 0.75,
            rp2040_practical_ring,
            math.ceil(_line_drain_bytes_per_s(t, 8.0) * 0.100),
            100.0,
            8.0,
        ),
        SpoolCase(
            "usb_hs_12ppm_128KiB_ring_passes_100ms",
            "USB_HS",
            USB_HS_BULK_NOMINAL_BYTES_PER_S,
            rp2040_practical_ring,
            required_100ms,
            100.0,
            float(t.ppm),
        ),
    ]
    evaluated = [evaluate_spool_case(c, t) for c in cases]
    return {
        "revision": "M1-REV-G",
        "finding": (
            "Rev E proved OFP1 byte correctness, not a real-time feed guarantee. "
            "A 32-line ring covers the old 10 ms target but not a sane 100 ms host pause; "
            "USB Full Speed at 75% of its theoretical bulk ceiling cannot sustain 12 ppm worst-case pages."
        ),
        "base_transport_budget": base,
        "rp2040_sram_bytes": RP2040_SRAM_BYTES,
        "row_bytes": row_bytes,
        "line_rate_lps": line_rate,
        "decoded_line_drain_bytes_per_s": drain,
        "decoded_line_drain_mbit_s": drain * 8.0 / 1_000_000.0,
        "required_buffer_bytes_for_100ms_pause": required_100ms,
        "revE_32_line_ring_buffer_bytes": rev_e_ring,
        "revE_pause_tolerance_ms": rev_e_ring / drain * 1000.0,
        "rp2040_128KiB_ring_pause_tolerance_ms": rp2040_practical_ring / drain * 1000.0,
        "solid_letter_payload_bytes_decoded": solid_page_payload,
        "solid_letter_wire_bytes_ofp1": solid_page_on_wire,
        "full_page_payload_fits_in_rp2040_sram": solid_page_payload < RP2040_SRAM_BYTES,
        "external_spool_ram_recommended_bytes": external_page_ram,
        "external_spool_ram_holds_solid_pages": external_page_ram // solid_page_on_wire,
        "max_safe_fs_service_ppm_at_60pct_ceiling": max_ppm_for_host_utilization(t),
        "cases": evaluated,
        "production_verdict": "Use USB High Speed or external page spool RAM before starting 12 ppm paper motion; USB Full Speed service/debug mode must either slow the engine and use a larger ring, or pre-spool before clutch start.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(realtime_spool_summary(), indent=2))
