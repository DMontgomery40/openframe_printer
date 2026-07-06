from __future__ import annotations

"""High-voltage channel table and Rev D consistency gates.

Rev C correctly found that the Rev A PCR value (-720 V DC) cannot charge a
negative OPC drum to the -600 V surface potential assumed by the exposure and
development model. But Rev C still let the generated artifact
``out/v2_hv_bias_channels.json`` emit the retired -720 V value. Rev D moves the
Rev C charging fixes into the generated model itself and adds checks that make
that regression hard to reintroduce.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class HVChannelOption:
    name: str
    option: str
    polarity: str
    nominal_v: float
    min_v: float
    max_v: float
    ac_component_kvpp: float
    ac_frequency_khz: float
    current_limit_uA: float
    ramp_v_per_s: float
    max_output_capacitance_nF: float
    control_signal: str
    monitor_signal: str
    output_contact: str
    purpose: str
    rationale: str

    @property
    def max_abs_v(self) -> float:
        return max(abs(self.nominal_v), abs(self.min_v), abs(self.max_v))

    @property
    def stored_energy_mJ_at_max_dc(self) -> float:
        # 0.5 * C * V^2, with C in nF. 1 nF*V^2 = 1e-9 J.
        return 0.5 * self.max_output_capacitance_nF * 1e-9 * (self.max_abs_v ** 2) * 1000.0


CHANNEL_OPTIONS: tuple[HVChannelOption, ...] = (
    HVChannelOption(
        name="PCR_CHARGE",
        option="A_dc_only",
        polarity="negative",
        nominal_v=-1180.0,
        min_v=-900.0,
        max_v=-1400.0,
        ac_component_kvpp=0.0,
        ac_frequency_khz=0.0,
        current_limit_uA=200.0,
        ramp_v_per_s=400.0,
        max_output_capacitance_nF=1.0,
        control_signal="PCR_DAC",
        monitor_signal="PCR_MON",
        output_contact="J8_PROCESS_CONTACTS_1",
        purpose="DC-only primary charge roller option for a negative-charge OPC drum.",
        rationale=(
            "DC contact charging starts only above the air-gap discharge threshold; "
            "a -600 V drum surface needs roughly |V0| + Vth at the roller. "
            "This retires the Rev A -720 V value."
        ),
    ),
    HVChannelOption(
        name="PCR_CHARGE",
        option="B_ac_dc",
        polarity="negative",
        nominal_v=-600.0,
        min_v=-450.0,
        max_v=-750.0,
        ac_component_kvpp=1.7,
        ac_frequency_khz=1.5,
        current_limit_uA=200.0,
        ramp_v_per_s=400.0,
        max_output_capacitance_nF=1.0,
        control_signal="PCR_DAC_PLUS_AC_STAGE",
        monitor_signal="PCR_MON",
        output_contact="J8_PROCESS_CONTACTS_1",
        purpose="AC+DC primary charge roller option; DC component sets the drum surface potential.",
        rationale=(
            "The physics minimum is about 1.3 kVpp across the 500-650 V threshold band; "
            "the build spec is 1.7 kVpp to include threshold, humidity, aging, and supply tolerance."
        ),
    ),
    HVChannelOption(
        name="DEVELOPER_BIAS",
        option="selected",
        polarity="negative",
        nominal_v=-320.0,
        min_v=-150.0,
        max_v=-500.0,
        ac_component_kvpp=0.0,
        ac_frequency_khz=0.0,
        current_limit_uA=300.0,
        ramp_v_per_s=200.0,
        max_output_capacitance_nF=1.0,
        control_signal="DEV_DAC",
        monitor_signal="DEV_MON",
        output_contact="J8_PROCESS_CONTACTS_2",
        purpose="Set toner development field between developer roller and latent image.",
        rationale=(
            "With a real -600 V charged surface, -320 V gives the first-build development "
            "contrast and fog margin used by the voltage ladder."
        ),
    ),
    HVChannelOption(
        name="TRANSFER_ROLLER",
        option="selected_current_limited",
        polarity="positive",
        nominal_v=1600.0,
        min_v=700.0,
        max_v=2500.0,
        ac_component_kvpp=0.0,
        ac_frequency_khz=0.0,
        current_limit_uA=500.0,
        ramp_v_per_s=500.0,
        max_output_capacitance_nF=0.75,
        control_signal="XFER_DAC",
        monitor_signal="XFER_MON",
        output_contact="J8_PROCESS_CONTACTS_3",
        purpose="Pull toner from drum to paper at the transfer nip.",
        rationale=(
            "Rev D keeps the voltage envelope but adds a current-limited impedance-sniff "
            "transfer control plan in transfer_model.py."
        ),
    ),
)


RETIRED_PCR_NOMINAL_V = -720.0


def hv_table() -> list[dict]:
    rows: list[dict] = []
    for ch in CHANNEL_OPTIONS:
        d = asdict(ch)
        d["stored_energy_mJ_at_max_dc"] = round(ch.stored_energy_mJ_at_max_dc, 3)
        d["hardware_gate_required"] = True
        d["fault_response"] = "remove HV_ENABLE, open interlock relay, discharge through potted module bleed path"
        rows.append(d)
    return rows


def pcr_charge_options() -> list[dict]:
    return [row for row in hv_table() if row["name"] == "PCR_CHARGE"]


def hv_consistency_summary(ladder: dict) -> dict:
    """Cross-check generated HV rows against the voltage ladder.

    This is intentionally a small build gate, not a full schematic verifier.
    It catches the exact Rev C regression: prose/CSV says the PCR was fixed,
    generated JSON still emits the retired -720 V PCR bias.
    """
    pcr_rows = pcr_charge_options()
    by_option = {row["option"]: row for row in pcr_rows}
    option_a_ladder_v = ladder["rev_c_option_a_dc_only"]["pcr_applied_v"]
    option_b_ladder = ladder["rev_c_option_b_ac_dc"]
    option_b_physics_min = option_b_ladder["pcr_ac_physics_min_kvpp"]
    option_b_spec = option_b_ladder["pcr_ac_spec_kvpp_with_headroom"]

    checks = {
        "retired_rev_a_pcr_bias_absent": all(row["nominal_v"] != RETIRED_PCR_NOMINAL_V for row in pcr_rows),
        "option_a_nominal_matches_ladder": by_option["A_dc_only"]["nominal_v"] == option_a_ladder_v,
        "option_b_dc_matches_ladder": by_option["B_ac_dc"]["nominal_v"] == option_b_ladder["pcr_dc_v"],
        "option_b_ac_spec_exceeds_physics_min": by_option["B_ac_dc"]["ac_component_kvpp"] >= option_b_physics_min,
        "option_b_ac_spec_matches_ladder_headroom": by_option["B_ac_dc"]["ac_component_kvpp"] == option_b_spec,
    }
    return {
        "revision": "M1-REV-D",
        "retired_pcr_nominal_v": RETIRED_PCR_NOMINAL_V,
        "pcr_options": pcr_rows,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "failure_meaning": (
            "If any check fails, generated HV artifacts no longer match the voltage ladder; "
            "do not order or energize the HV module."
        ),
    }


def interlock_matrix() -> list[dict]:
    signals = [
        "COVER_CLOSED_LOOP",
        "FUSER_THERMOSTAT_CLOSED",
        "THERMAL_FUSE_CONTINUITY",
        "24V_PRESENT",
        "ESTOP_LOOP_CLOSED",
        "MCU_WATCHDOG_OK",
    ]
    outputs = ["HV_ENABLE", "LED_OE", "FUSER_HEATER_ENABLE", "MAIN_MOTOR_ENABLE"]
    rows = []
    for sig in signals:
        for out in outputs:
            rows.append({
                "input": sig,
                "output_gated": out,
                "gate_type": "hardware AND before firmware permission",
                "safe_state_when_false": "forced_off",
            })
    return rows


if __name__ == "__main__":
    import json
    from .voltage_ladder import ladder_summary

    print(json.dumps({"channels": hv_table(), "consistency": hv_consistency_summary(ladder_summary())}, indent=2))
