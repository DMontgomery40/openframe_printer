from __future__ import annotations

"""Rev D current-limited transfer control with paper-impedance sniffing.

A fixed transfer voltage is fragile because the effective transfer impedance is
owned by paper moisture, paper thickness, transfer-roller resistivity, and nip
conditions. Rev D turns the earlier H5 idea into a concrete first-build control
law: sniff the blank paper/nip impedance with a safe diagnostic pulse, then run
transfer in current mode with a voltage limiter.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class TransferCurrentChoice:
    case: str
    measured_impedance_mohm: float
    target_transfer_voltage_v: float
    max_transfer_voltage_v: float
    min_transfer_current_uA: float
    max_transfer_current_uA: float
    ideal_current_for_target_voltage_uA: float
    chosen_transfer_current_uA: float
    expected_transfer_voltage_v: float
    voltage_limited: bool
    current_floor_met: bool
    verdict: str


def choose_transfer_current(
    measured_impedance_mohm: float,
    case: str = "measured",
    target_transfer_voltage_v: float = 1600.0,
    max_transfer_voltage_v: float = 2500.0,
    min_transfer_current_uA: float = 5.0,
    max_transfer_current_uA: float = 200.0,
) -> TransferCurrentChoice:
    if measured_impedance_mohm <= 0.0:
        raise ValueError("measured_impedance_mohm must be positive")
    ideal_current = target_transfer_voltage_v / measured_impedance_mohm  # V / Mohm = uA
    max_safe_current = max_transfer_voltage_v / measured_impedance_mohm
    chosen = min(max_transfer_current_uA, max(min_transfer_current_uA, ideal_current))
    voltage_limited = False
    if chosen > max_safe_current:
        chosen = max_safe_current
        voltage_limited = True
    expected_voltage = chosen * measured_impedance_mohm
    current_floor_met = chosen >= min_transfer_current_uA - 1e-9
    verdict = "run"
    if not current_floor_met:
        verdict = "reject_or_slow_engine_for_transfer_latitude"
    elif voltage_limited:
        verdict = "run_voltage_limited"
    return TransferCurrentChoice(
        case=case,
        measured_impedance_mohm=measured_impedance_mohm,
        target_transfer_voltage_v=target_transfer_voltage_v,
        max_transfer_voltage_v=max_transfer_voltage_v,
        min_transfer_current_uA=min_transfer_current_uA,
        max_transfer_current_uA=max_transfer_current_uA,
        ideal_current_for_target_voltage_uA=round(ideal_current, 3),
        chosen_transfer_current_uA=round(chosen, 3),
        expected_transfer_voltage_v=round(expected_voltage, 1),
        voltage_limited=voltage_limited,
        current_floor_met=current_floor_met,
        verdict=verdict,
    )


def transfer_impedance_plan() -> dict:
    scenarios = [
        ("humid_or_low_resistance_paper", 8.0),
        ("normal_plain_paper", 30.0),
        ("dry_heavy_paper", 100.0),
        ("very_dry_high_impedance_paper", 300.0),
        ("extreme_impedance_reject_or_slow", 800.0),
    ]
    choices = [asdict(choose_transfer_current(z, case=name)) for name, z in scenarios]
    return {
        "revision": "M1-REV-D",
        "control_law": (
            "Before image transfer, apply a low diagnostic pulse at the transfer nip, "
            "estimate Z = V/I, then choose current mode so I ~= 1600 V / Z while "
            "clamping current and never exceeding the 2500 V transfer envelope."
        ),
        "sniff_pulse": {
            "diagnostic_current_uA": 20.0,
            "diagnostic_duration_ms": 10.0,
            "requires_blank_drum_or_preimage_gap": True,
            "measurement": "use XFER_MON voltage and commanded current to estimate paper+nip impedance",
        },
        "choices": choices,
        "hard_gate": (
            "If the required current falls below 5 uA before hitting the 2500 V limiter, "
            "do not blindly raise voltage; slow the process speed, warn on media/environment, "
            "or reject the sheet for the prototype."
        ),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(transfer_impedance_plan(), indent=2))
