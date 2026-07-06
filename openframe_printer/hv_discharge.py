from __future__ import annotations

"""Rev G: stored-charge bleed-down budget for HV nodes.

Interlocks remove enable power, but a high-voltage output node can remain charged
if its output capacitance has no deliberate discharge path. This module sizes a
redundant bleed network so each modeled node falls below the ordinary-person
60 V target in normal operation and below 120 V with one bleeder open.
"""

import math
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class HVNode:
    name: str
    initial_v: float
    capacitance_nf: float
    bleeder_each_mohm: float
    bleeder_count: int = 2
    target_normal_v: float = 60.0
    target_single_fault_v: float = 120.0
    discharge_time_s: float = 2.0


def voltage_after_s(initial_v: float, capacitance_nf: float, resistance_mohm: float, time_s: float) -> float:
    c_f = capacitance_nf * 1e-9
    r_ohm = resistance_mohm * 1e6
    if c_f <= 0 or r_ohm <= 0:
        raise ValueError("capacitance and resistance must be positive")
    return initial_v * math.exp(-time_s / (r_ohm * c_f))


def max_resistance_for_decay_mohm(initial_v: float, target_v: float,
                                  capacitance_nf: float, time_s: float) -> float:
    if abs(initial_v) <= target_v:
        return float("inf")
    c_f = capacitance_nf * 1e-9
    return time_s / (c_f * math.log(abs(initial_v) / target_v)) / 1e6


def evaluate_node(node: HVNode) -> dict:
    normal_equiv_mohm = node.bleeder_each_mohm / node.bleeder_count
    single_fault_mohm = node.bleeder_each_mohm  # one of two parallel bleeders opened
    v_normal = abs(voltage_after_s(node.initial_v, node.capacitance_nf, normal_equiv_mohm, node.discharge_time_s))
    v_fault = abs(voltage_after_s(node.initial_v, node.capacitance_nf, single_fault_mohm, node.discharge_time_s))
    max_normal = max_resistance_for_decay_mohm(abs(node.initial_v), node.target_normal_v, node.capacitance_nf, node.discharge_time_s)
    max_fault = max_resistance_for_decay_mohm(abs(node.initial_v), node.target_single_fault_v, node.capacitance_nf, node.discharge_time_s)
    normal_current_ua = abs(node.initial_v) / (normal_equiv_mohm * 1e6) * 1e6
    total_power_mw = abs(node.initial_v) * normal_current_ua / 1000.0
    return {
        **asdict(node),
        "normal_equivalent_bleed_mohm": normal_equiv_mohm,
        "single_fault_remaining_bleed_mohm": single_fault_mohm,
        "voltage_after_2s_normal_v": v_normal,
        "voltage_after_2s_single_fault_v": v_fault,
        "max_equivalent_bleed_for_60v_in_2s_mohm": max_normal,
        "max_single_bleeder_for_120v_in_2s_mohm": max_fault,
        "normal_bleed_current_ua": normal_current_ua,
        "total_bleeder_power_mw": total_power_mw,
        "each_bleeder_power_mw": total_power_mw / node.bleeder_count,
        "passes_normal_60v_gate": v_normal <= node.target_normal_v,
        "passes_single_fault_120v_gate": v_fault <= node.target_single_fault_v,
    }


def no_bleed_counterexample(initial_v: float = 2500.0, capacitance_nf: float = 2.2,
                            time_s: float = 2.0) -> dict:
    # Ideal leakage omitted: this is the design-review counterexample. With no
    # specified bleed path, the generated artifacts have no guaranteed decay.
    energy_mj = 0.5 * capacitance_nf * 1e-9 * initial_v ** 2 * 1000.0
    return {
        "initial_v": initial_v,
        "capacitance_nf": capacitance_nf,
        "stored_energy_mj": energy_mj,
        "voltage_after_2s_without_specified_bleed_v": initial_v,
        "verdict": "fail_no_guaranteed_touch_safe_decay",
    }


def default_nodes() -> list[HVNode]:
    return [
        HVNode("TRANSFER_ROLLER_OUTPUT", 2500.0, 2.2, 100.0),
        HVNode("PCR_DC_OUTPUT_OPTION_A", -1400.0, 2.2, 100.0),
        HVNode("PCR_AC_PEAK_OUTPUT_OPTION_B", 1450.0, 1.0, 150.0),
        HVNode("DEVELOPER_BIAS_OUTPUT", -500.0, 1.0, 220.0),
    ]


def hv_discharge_summary(nodes: list[HVNode] | None = None) -> dict:
    evaluated = [evaluate_node(n) for n in (nodes or default_nodes())]
    return {
        "requirement": "every HV output node has redundant bleeders and a measured discharge test",
        "counterexample_no_bleeder": no_bleed_counterexample(),
        "nodes": evaluated,
        "all_nodes_pass_normal_60v": all(n["passes_normal_60v_gate"] for n in evaluated),
        "all_nodes_pass_single_fault_120v": all(n["passes_single_fault_120v_gate"] for n in evaluated),
        "hardware_delta": "add two independent HV-rated bleeders per output node; verify with HV probe after interlock trip and after mains removal",
    }
