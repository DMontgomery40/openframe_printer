from __future__ import annotations

"""Single-fault and common-cause analysis of the interlock chain.

Rev E proved something useful but narrower than its prose implied: the proposed
second interlock chain survives the enumerated *electrical* stuck-at faults. It
did not model the mechanical common-cause failure that real door interlocks are
notorious for: one cracked/misaligned actuator tab, defeated latch, or pinched
harness path that makes both switch contacts for the same door read closed.

Rev F keeps Rev E's electrical proof, then adds that common-cause fault class.
Result: the Rev E dual-chain topology is electrically better but still not a
safety architecture. The Rev F topology adds a third, diverse energy-removal
path: a physical energy contact / shroud / contactor opened by the access door
and not actuated by the same switch tab. Hazards are live only when the logic
chain, the independent relay chain, and the physical energy path all agree.
"""

from itertools import combinations
from typing import Callable

DOORS = ("main_cover", "rear_door", "service_panel")
HAZARDS = ("hv", "led", "fuser")

# Fault points: (net, forced_value). stuck_closed on a switch contact means the
# contact stays conductive with its door open. stuck_1 on a gate or loop means
# the enable is asserted regardless of inputs.
FAULTS_A = [
    *[(f"sw_{door}", "stuck_closed") for door in DOORS],
    *[(f"sw_{door}", "stuck_open") for door in DOORS],
    ("loop", "stuck_1"),
    ("loop", "stuck_0"),
    *[(f"gate_{h}", "stuck_1") for h in HAZARDS],
    *[(f"gate_{h}", "stuck_0") for h in HAZARDS],
]

FAULTS_B_ELECTRICAL = [
    *[(f"sw_{door}_a", "stuck_closed") for door in DOORS],
    *[(f"sw_{door}_b", "stuck_closed") for door in DOORS],
    *[(f"sw_{door}_a", "stuck_open") for door in DOORS],
    *[(f"sw_{door}_b", "stuck_open") for door in DOORS],
    ("loop_a", "stuck_1"),
    ("loop_b", "stuck_1"),
    ("loop_a", "stuck_0"),
    ("loop_b", "stuck_0"),
    *[(f"gate_{h}", "stuck_1") for h in HAZARDS],
    *[(f"gate_{h}", "stuck_0") for h in HAZARDS],
    ("power_relay", "stuck_1"),
    ("power_relay", "stuck_0"),
]

COMMON_CAUSE_DOOR_FAULTS = [
    (f"door_{door}_common_actuator", "stuck_closed_both_chains") for door in DOORS
]

FAULTS_B_WITH_COMMON_CAUSE = [*FAULTS_B_ELECTRICAL, *COMMON_CAUSE_DOOR_FAULTS]

FAULTS_C = [
    *FAULTS_B_WITH_COMMON_CAUSE,
    *[(f"energy_contact_{door}", "stuck_closed") for door in DOORS],
    *[(f"energy_contact_{door}", "stuck_open") for door in DOORS],
    ("energy_path", "stuck_1"),
    ("energy_path", "stuck_0"),
]


def _contact(door_closed: bool, fault: str | None) -> bool:
    if fault == "stuck_closed":
        return True
    if fault == "stuck_open":
        return False
    return door_closed


def _forced(value: bool, fault: str | None) -> bool:
    if fault == "stuck_1":
        return True
    if fault == "stuck_0":
        return False
    return value


def _door_chain_contact(door: str, chain: str, doors_closed: dict[str, bool], faults: dict[str, str]) -> bool:
    if faults.get(f"door_{door}_common_actuator") == "stuck_closed_both_chains":
        return True
    return _contact(doors_closed[door], faults.get(f"sw_{door}_{chain}"))


def eval_topology_a(doors_closed: dict[str, bool], faults: dict[str, str]) -> dict[str, bool]:
    loop = all(_contact(doors_closed[d], faults.get(f"sw_{d}")) for d in DOORS)
    loop = _forced(loop, faults.get("loop"))
    return {
        h: _forced(True and loop, faults.get(f"gate_{h}"))  # request always high
        for h in HAZARDS
    }


def eval_topology_b(doors_closed: dict[str, bool], faults: dict[str, str]) -> dict[str, bool]:
    """Rev E dual electrical chain: logic gates + relay/SSR energy path."""
    loop_a = all(_door_chain_contact(d, "a", doors_closed, faults) for d in DOORS)
    loop_b = all(_door_chain_contact(d, "b", doors_closed, faults) for d in DOORS)
    loop_a = _forced(loop_a, faults.get("loop_a"))
    loop_b = _forced(loop_b, faults.get("loop_b"))
    power = _forced(loop_b, faults.get("power_relay"))
    return {
        h: _forced(True and loop_a, faults.get(f"gate_{h}")) and power
        for h in HAZARDS
    }


def eval_topology_c(doors_closed: dict[str, bool], faults: dict[str, str]) -> dict[str, bool]:
    """Rev F diverse topology: Rev E dual chain plus physical energy separation.

    The physical energy path is not operated by the same switch actuator that can
    common-cause the two sense contacts. It represents a mechanically separated
    contact block, shrouded cartridge HV contact, or positive-opening contactor
    whose open state removes the hazardous energy path regardless of firmware.
    """
    loop_a = all(_door_chain_contact(d, "a", doors_closed, faults) for d in DOORS)
    loop_b = all(_door_chain_contact(d, "b", doors_closed, faults) for d in DOORS)
    physical_energy = all(_contact(doors_closed[d], faults.get(f"energy_contact_{d}")) for d in DOORS)
    loop_a = _forced(loop_a, faults.get("loop_a"))
    loop_b = _forced(loop_b, faults.get("loop_b"))
    relay = _forced(loop_b, faults.get("power_relay"))
    energy_path = _forced(physical_energy, faults.get("energy_path"))
    return {
        h: _forced(True and loop_a, faults.get(f"gate_{h}")) and relay and energy_path
        for h in HAZARDS
    }


def _violations(
    evaluate: Callable[[dict[str, bool], dict[str, str]], dict[str, bool]],
    fault_universe: list[tuple[str, str]],
    fault_count: int,
) -> list[dict]:
    """Every fault set of the given size that energizes a hazard with a door open."""
    found = []
    for fault_set in combinations(fault_universe, fault_count):
        nets = [net for net, _ in fault_set]
        if len(set(nets)) != len(nets):
            continue  # one physical fault per net
        faults = dict(fault_set)
        for open_door in DOORS:
            doors = {d: d != open_door for d in DOORS}
            live = [h for h, on in evaluate(doors, faults).items() if on]
            if live:
                found.append({
                    "faults": [f"{net}:{mode}" for net, mode in fault_set],
                    "open_door": open_door,
                    "hazards_live": live,
                })
    return found


def _single_point_nets(violations: list[dict]) -> list[str]:
    return sorted({v["faults"][0] for v in violations})


def interlock_fault_summary() -> dict:
    a_single = _violations(eval_topology_a, FAULTS_A, 1)
    b_electrical_single = _violations(eval_topology_b, FAULTS_B_ELECTRICAL, 1)
    b_electrical_double = _violations(eval_topology_b, FAULTS_B_ELECTRICAL, 2)
    b_common_single = _violations(eval_topology_b, FAULTS_B_WITH_COMMON_CAUSE, 1)
    c_single = _violations(eval_topology_c, FAULTS_C, 1)
    c_double = _violations(eval_topology_c, FAULTS_C, 2)
    return {
        "revision": "M1-REV-F",
        "assumption": "firmware adversarial: all hazard request lines driven high",
        "topology_a_as_documented": {
            "description": "one NC switch per door, single series loop, one AND gate per hazard",
            "single_fault_violation_count": len(a_single),
            "single_point_failure_nets": _single_point_nets(a_single),
            "verdict_single_fault_safe": len(a_single) == 0,
        },
        "topology_b_rev_e_proposal": {
            "description": (
                "two contacts per door in two independent electrical chains; chain A gates "
                "logic enables, chain B cuts the energy path via relay/SSR"
            ),
            "single_fault_violation_count": len(b_electrical_single),
            "verdict_single_fault_safe": len(b_electrical_single) == 0,
            "double_fault_violation_count": len(b_electrical_double),
            "note_revF": "This is Rev E's independent electrical stuck-at model only; see common-cause section below.",
        },
        "topology_b_rev_e_electrical_fault_model": {
            "description": (
                "two contacts per door in two independent electrical chains; chain A gates "
                "logic enables, chain B cuts the energy path via relay/SSR"
            ),
            "single_fault_violation_count": len(b_electrical_single),
            "verdict_single_fault_safe_with_only_electrical_stuck_at_faults": len(b_electrical_single) == 0,
            "double_fault_violation_count": len(b_electrical_double),
        },
        "topology_b_rev_e_with_mechanical_common_cause": {
            "description": (
                "same dual-chain electrical topology, but one door actuator/common harness fault "
                "can force both contacts for that door closed"
            ),
            "single_fault_violation_count": len(b_common_single),
            "single_point_failure_nets": _single_point_nets(b_common_single),
            "verdict_single_fault_safe_with_common_cause": len(b_common_single) == 0,
        },
        "topology_c_rev_f_diverse_energy_path": {
            "description": (
                "Rev E dual electrical chain plus a physically diverse door-open energy separator "
                "not actuated by the same switch tab"
            ),
            "single_fault_violation_count": len(c_single),
            "verdict_single_fault_safe_with_common_cause": len(c_single) == 0,
            "double_fault_violation_count": len(c_double),
            "example_defeating_double_faults": [v["faults"] for v in c_double[:4]],
        },
        "recommendation": (
            "Adopt topology C before the first HV or fuser rig. Rev E's dual chain is a good "
            "electrical improvement, but two switch contacts moved by the same plastic tab are "
            "not diverse safeguards. The hazardous energy path needs a physically separated "
            "door-open break or shrouded module contact."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(interlock_fault_summary(), indent=2))
