from __future__ import annotations

"""Single-fault analysis of the interlock chain.

The safety docs assert "firmware cannot override cover-open state" and the
interlock matrix lists which loop gates which hazard. None of that answers
the appliance-safety question a certification reviewer will actually ask:
*which single component failure, combined with an open cover and the worst
possible firmware, energizes a hazard?* IEC 62368-class thinking wants
safeguards to survive any one fault.

Rev E answers it exhaustively. Two topologies are modeled:

Topology A -- the chain as drawn in `hardware/interlock_chain.md`: one NC
switch per access door, one series loop, one AND gate per hazard.

Topology B -- the Rev E proposal: each door opens TWO independent contacts,
wired into two independent cut paths (chain A feeds the logic enable gates,
chain B feeds a series power relay/SSR in the actual energy path). A hazard
is live only if its request, its logic gate, and the power path all agree.

Firmware is modeled as adversarial: every request line is driven high.
A violation is any fault that leaves a hazard energized while any door is
open. The engine enumerates every single stuck-at fault and reports both
topologies' violation lists; the model tests pin the honest result --
Topology A has single points of failure, Topology B has none.
"""

from itertools import combinations

DOORS = ("main_cover", "rear_door", "service_panel")
HAZARDS = ("hv", "led", "fuser")

# Fault points: (net, forced_value). stuck_closed on a switch contact means
# the contact stays conductive with its door open (welded contact / pinched
# harness). stuck_1 on a gate or loop means the enable is asserted regardless
# of inputs (shorted driver, solder bridge, damaged wire to a live rail).
FAULTS_A = [
    *[(f"sw_{door}", "stuck_closed") for door in DOORS],
    *[(f"sw_{door}", "stuck_open") for door in DOORS],
    ("loop", "stuck_1"),
    ("loop", "stuck_0"),
    *[(f"gate_{h}", "stuck_1") for h in HAZARDS],
    *[(f"gate_{h}", "stuck_0") for h in HAZARDS],
]

FAULTS_B = [
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


def eval_topology_a(doors_closed: dict[str, bool], faults: dict[str, str]) -> dict[str, bool]:
    loop = all(_contact(doors_closed[d], faults.get(f"sw_{d}")) for d in DOORS)
    loop = _forced(loop, faults.get("loop"))
    return {
        h: _forced(True and loop, faults.get(f"gate_{h}"))  # request always high
        for h in HAZARDS
    }


def eval_topology_b(doors_closed: dict[str, bool], faults: dict[str, str]) -> dict[str, bool]:
    loop_a = all(_contact(doors_closed[d], faults.get(f"sw_{d}_a")) for d in DOORS)
    loop_b = all(_contact(doors_closed[d], faults.get(f"sw_{d}_b")) for d in DOORS)
    loop_a = _forced(loop_a, faults.get("loop_a"))
    loop_b = _forced(loop_b, faults.get("loop_b"))
    power = _forced(loop_b, faults.get("power_relay"))
    return {
        h: _forced(True and loop_a, faults.get(f"gate_{h}")) and power
        for h in HAZARDS
    }


def _violations(evaluate, fault_universe, fault_count: int) -> list[dict]:
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


def interlock_fault_summary() -> dict:
    a_single = _violations(eval_topology_a, FAULTS_A, 1)
    b_single = _violations(eval_topology_b, FAULTS_B, 1)
    b_double = _violations(eval_topology_b, FAULTS_B, 2)
    # Deduplicate by fault signature for the counts humans read.
    a_nets = sorted({v["faults"][0] for v in a_single})
    return {
        "assumption": "firmware adversarial: all hazard request lines driven high",
        "topology_a_as_documented": {
            "description": "one NC switch per door, single series loop, one AND gate per hazard",
            "single_fault_violation_count": len(a_single),
            "single_point_failure_nets": a_nets,
            "verdict_single_fault_safe": len(a_single) == 0,
        },
        "topology_b_rev_e_proposal": {
            "description": (
                "two contacts per door in two independent chains; chain A gates "
                "logic enables, chain B cuts the energy path via relay/SSR"
            ),
            "single_fault_violation_count": len(b_single),
            "verdict_single_fault_safe": len(b_single) == 0,
            "double_fault_violation_count": len(b_double),
            "example_defeating_double_faults": [v["faults"] for v in b_double[:4]],
        },
        "recommendation": (
            "Adopt topology B before the first HV or fuser rig: welded-contact "
            "and shorted-enable faults are exactly the failures aging plastic "
            "switches and vibration produce, and topology A converts any one of "
            "them into a silent live-with-cover-open machine."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(interlock_fault_summary(), indent=2))
