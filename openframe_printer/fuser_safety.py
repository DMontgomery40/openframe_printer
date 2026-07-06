from __future__ import annotations

"""Rev G fuser thermal runaway fault model.

Rev F modeled continuous heater power, but power balance is not a thermal
runaway safety proof. This module enumerates single faults around the fuser
heater, thermistor, controller switch, independent thermostat, and one-shot
thermal fuse. It makes the RFQ safety devices executable instead of merely
listed.
"""

from dataclasses import dataclass
from itertools import combinations


HAZARDS = ("heater_continues_above_fault_temp",)
FAULTS = (
    "thermistor_stuck_cold",
    "thermistor_stuck_hot",
    "firmware_output_stuck_on",
    "ssr_welded_on",
    "thermostat_welded_closed",
    "thermal_fuse_bypassed_closed",
    "thermal_fuse_open_nuisance",
)


@dataclass(frozen=True)
class FuserSafetyTopology:
    name: str
    has_independent_thermostat: bool
    has_one_shot_thermal_fuse: bool
    has_series_energy_relay: bool = True


def _faults_set(faults: tuple[str, ...] | list[str] | set[str]) -> set[str]:
    return set(faults)


def eval_fuser_topology(topology: FuserSafetyTopology, faults: tuple[str, ...] | list[str] | set[str]) -> dict[str, bool]:
    f = _faults_set(faults)
    # Evaluate the system at an actually over-temperature fuser. A good thermistor
    # makes firmware command heat off. Stuck-cold or stuck-on output defeats that.
    thermistor_reports_cold = "thermistor_stuck_cold" in f
    firmware_commands_heat = thermistor_reports_cold or "firmware_output_stuck_on" in f
    control_switch_conducts = firmware_commands_heat or "ssr_welded_on" in f

    thermostat_closed = True
    if topology.has_independent_thermostat and "thermostat_welded_closed" not in f:
        thermostat_closed = False  # independent bimetal has opened on over-temperature

    fuse_closed = True
    if topology.has_one_shot_thermal_fuse and "thermal_fuse_bypassed_closed" not in f:
        fuse_closed = False  # one-shot cutoff has opened at runaway temperature
    if "thermal_fuse_open_nuisance" in f:
        fuse_closed = False

    energy_relay_closed = topology.has_series_energy_relay
    heater_live = control_switch_conducts and thermostat_closed and fuse_closed and energy_relay_closed
    return {"heater_continues_above_fault_temp": heater_live}


def _violations(topology: FuserSafetyTopology, fault_count: int) -> list[dict]:
    violations: list[dict] = []
    for combo in combinations(FAULTS, fault_count):
        live = eval_fuser_topology(topology, combo)
        if any(live.values()):
            violations.append({"faults": list(combo), "hazards": live})
    return violations


def fuser_safety_summary() -> dict:
    firmware_only = FuserSafetyTopology("revF_power_model_without_independent_cutoffs", False, False)
    thermostat_only = FuserSafetyTopology("single_independent_thermostat_only", True, False)
    revg = FuserSafetyTopology("revG_thermostat_plus_one_shot_fuse", True, True)
    fw_single = _violations(firmware_only, 1)
    thermo_single = _violations(thermostat_only, 1)
    revg_single = _violations(revg, 1)
    revg_double = _violations(revg, 2)
    return {
        "revision": "M1-REV-G",
        "fault_temperature_c": 205.0,
        "independent_thermostat_open_c": 195.0,
        "one_shot_fuse_open_c": 216.0,
        "assumption": "evaluate at over-temperature with firmware adversarial or failed high where the fault says so",
        "topology_firmware_only": {
            "description": "thermistor plus firmware/SSR only; no independent heat cutoff",
            "single_fault_violation_count": len(fw_single),
            "single_fault_violations": fw_single,
            "verdict_single_fault_safe": len(fw_single) == 0,
        },
        "topology_thermostat_only": {
            "description": "firmware control plus one independent resettable thermostat",
            "single_fault_violation_count": len(thermo_single),
            "verdict_single_fault_safe": len(thermo_single) == 0,
            "note": "single-fault safe in this model, but a welded thermostat plus SSR/thermistor fault remains a foreseeable double fault; add one-shot fuse for non-reset backup.",
        },
        "topology_revG_thermostat_plus_one_shot_fuse": {
            "description": "firmware control, independent thermostat, and independent one-shot thermal fuse in the heater energy path",
            "single_fault_violation_count": len(revg_single),
            "verdict_single_fault_safe": len(revg_single) == 0,
            "double_fault_violation_count": len(revg_double),
            "example_defeating_double_faults": [v["faults"] for v in revg_double[:6]],
        },
        "rfq_gate": "Fuser quotes must provide thermistor curve, independent thermostat opening temperature, one-shot thermal fuse rating, and proof both cutoff loops are physically in series with heater energy.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(fuser_safety_summary(), indent=2))
