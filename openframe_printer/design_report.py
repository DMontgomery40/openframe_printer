from __future__ import annotations

import csv
import json
from pathlib import Path
from .engine_math import EngineTargets, design_calcs
from .exposure_model import exposure_summary, led_group_map
from .fuser_model import simulate_fuser
from .hv_model import hv_table, interlock_matrix, hv_consistency_summary
from .motion_model import transit_events
from .nozzle_math import nozzle_summary
from .ep_physics import physics_summary
from .station_map import solve_station_map, station_map_rows
from .pidc_model import synthetic_rig_demo
from .voltage_ladder import ladder_summary
from .dev_probe import dev_probe_summary
from .transfer_model import transfer_impedance_plan
from .units import lint_artifact

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"


def write_json(name: str, data: object) -> Path:
    OUT.mkdir(exist_ok=True)
    problems = lint_artifact(data, path=name)
    if problems:
        raise ValueError(
            "unit plausibility lint failed:\n  " + "\n  ".join(problems)
        )
    p = OUT / name
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def write_csv(name: str, rows: list[dict]) -> Path:
    OUT.mkdir(exist_ok=True)
    p = OUT / name
    if not rows:
        p.write_text("", encoding="utf-8")
        return p
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return p


def draw_cross_section_svg(target: EngineTargets) -> str:
    # Simple side-view, not pretty CAD. Coordinates are millimeters scaled into SVG units.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="420" viewBox="0 0 920 420">
  <title>OpenFrame M1 Rev A paper path / engine side view</title>
  <style>
    text {{ font-family: Arial, sans-serif; font-size: 13px; }}
    .label {{ font-size: 12px; }}
    .module {{ fill: none; stroke: #111; stroke-width: 2; }}
    .path {{ fill: none; stroke: #111; stroke-width: 3; }}
    .thin {{ fill: none; stroke: #111; stroke-width: 1; }}
  </style>
  <rect class="module" x="35" y="55" width="830" height="290" rx="8"/>
  <text x="45" y="40">OpenFrame M1 Rev A: 600 dpi monochrome LED electrophotographic engine, 12 ppm, process speed {design_calcs(target)['process_speed_mm_s_letter']:.1f} mm/s</text>
  <polyline class="path" points="65,300 150,300 230,275 320,240 430,210 560,205 675,210 790,185 835,170"/>
  <rect class="thin" x="55" y="286" width="120" height="42" rx="4"/>
  <text class="label" x="68" y="312">250-sheet tray</text>
  <circle class="module" cx="150" cy="280" r="18"/>
  <text class="label" x="125" y="250">pickup Ø18</text>
  <circle class="module" cx="250" cy="255" r="12"/>
  <text class="label" x="220" y="232">registration Ø12</text>
  <rect class="module" x="315" y="110" width="245" height="140" rx="5"/>
  <text class="label" x="330" y="130">open process cartridge</text>
  <circle class="module" cx="445" cy="190" r="{target.drum_diameter_mm/2*2.4:.1f}"/>
  <text class="label" x="415" y="190">OPC drum Ø{target.drum_diameter_mm:.0f}</text>
  <rect class="module" x="330" y="95" width="215" height="22" rx="3"/>
  <text class="label" x="350" y="91">5120-pixel LED bar, 780 nm</text>
  <circle class="thin" cx="392" cy="198" r="20"/>
  <text class="label" x="342" y="230">developer</text>
  <circle class="thin" cx="445" cy="142" r="14"/>
  <text class="label" x="455" y="145">PCR</text>
  <circle class="thin" cx="497" cy="210" r="16"/>
  <text class="label" x="505" y="232">transfer</text>
  <rect class="module" x="605" y="138" width="122" height="112" rx="6"/>
  <circle class="module" cx="650" cy="185" r="24"/>
  <circle class="module" cx="690" cy="212" r="24"/>
  <text class="label" x="617" y="130">fuser module {target.nominal_fuser_surface_temp_c:.0f}°C</text>
  <text class="label" x="620" y="268">nip {target.fuser_nip_width_mm:.1f} mm / dwell {design_calcs(target)['fuser_nip_dwell_ms']:.1f} ms</text>
  <circle class="module" cx="790" cy="170" r="16"/>
  <text class="label" x="760" y="145">exit roller</text>
  <line class="thin" x1="445" y1="95" x2="445" y2="160"/>
  <text class="label" x="455" y="108">expose charged drum</text>
  <text class="label" x="52" y="368">All hot/HV/light-emitting modules are behind hardware interlocks. This drawing is a geometry contract, not a certification.</text>
</svg>
'''


def draw_process_cartridge_svg(target: EngineTargets) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="360" viewBox="0 0 820 360">
  <title>OpenFrame M1 Rev A open process cartridge concept</title>
  <style>text {{ font-family: Arial, sans-serif; font-size: 13px; }} .a {{ fill: none; stroke: #111; stroke-width: 2; }} .b {{ fill: none; stroke: #111; stroke-width: 1; }}</style>
  <rect class="a" x="50" y="45" width="710" height="260" rx="8"/>
  <text x="60" y="30">Open process cartridge: replaceable OPC drum, developer roller, doctor blade, waste toner path, toner hopper</text>
  <circle class="a" cx="390" cy="180" r="72"/>
  <text x="360" y="184">OPC drum</text>
  <text x="345" y="202">Ø{target.drum_diameter_mm:.0f} mm</text>
  <circle class="a" cx="245" cy="190" r="38"/>
  <text x="190" y="246">developer roller Ø{target.developer_roller_diameter_mm:.0f} mm</text>
  <rect class="b" x="125" y="90" width="165" height="68" rx="4"/>
  <text x="150" y="128">toner hopper</text>
  <line class="a" x1="280" y1="145" x2="315" y2="155"/>
  <text x="245" y="118">doctor blade gap sweep 80-180 µm</text>
  <circle class="a" cx="390" cy="72" r="24"/>
  <text x="420" y="78">primary charge roller Ø{target.primary_charge_roller_diameter_mm:.0f} mm</text>
  <circle class="a" cx="515" cy="205" r="34"/>
  <text x="550" y="210">transfer roller Ø{target.transfer_roller_diameter_mm:.0f} mm</text>
  <rect class="b" x="315" y="275" width="150" height="20" rx="3"/>
  <text x="320" y="326">waste toner auger channel</text>
  <text x="60" y="326">Target toner: 6-8 µm black polymerized toner, dense black laydown {target.toner_dense_black_mg_cm2:.2f} mg/cm².</text>
</svg>
'''


def build_report() -> list[Path]:
    OUT.mkdir(exist_ok=True)
    t = EngineTargets()
    paths: list[Path] = []
    calcs = design_calcs(t)
    exposure = exposure_summary(t)
    motion = transit_events(t)
    fuser = simulate_fuser()
    hv = hv_table()
    nozzles = nozzle_summary()
    physics = physics_summary(t)
    ladder = ladder_summary()

    paths.append(write_json("v2_design_calcs.json", calcs))
    paths.append(write_json("v2_exposure_summary.json", exposure))
    paths.append(write_json("v2_motion_events.json", motion))
    paths.append(write_json("v2_hv_bias_channels.json", hv))
    paths.append(write_json("v2_nozzle_math.json", nozzles))
    paths.append(write_json("v2_ep_physics_summary.json", physics))
    paths.append(write_json("v2_fuser_summary.json", {k: v for k, v in fuser.items() if k != "rows"}))

    station_solution = solve_station_map(t)
    paths.append(write_json("v2_station_map.json", station_solution))
    paths.append(write_csv("v2_station_map.csv", station_map_rows(station_solution)))
    paths.append(write_json("v2_pidc_calibration_demo.json", synthetic_rig_demo()))
    paths.append(write_json("v2_voltage_ladder.json", ladder))
    paths.append(write_json("v2_hv_consistency.json", hv_consistency_summary(ladder)))
    paths.append(write_json("v2_dev_probe_budget.json", dev_probe_summary()))
    paths.append(write_json("v2_transfer_impedance_plan.json", transfer_impedance_plan()))

    paths.append(write_csv("v2_led_group_map.csv", led_group_map(t)))
    paths.append(write_csv("v2_fuser_sim.csv", fuser["rows"]))
    paths.append(write_csv("v2_interlock_matrix.csv", interlock_matrix()))

    cross = OUT / "v2_openframe_m1_cross_section.svg"
    cross.write_text(draw_cross_section_svg(t), encoding="utf-8")
    paths.append(cross)
    cart = OUT / "v2_process_cartridge.svg"
    cart.write_text(draw_process_cartridge_svg(t), encoding="utf-8")
    paths.append(cart)

    report = OUT / "v2_design_report.md"
    report.write_text(f"""# OpenFrame M1 Newbuild v2 design report

This report is generated from the Rev A constants in `openframe_printer/engine_math.py`.
It describes a new printer design, not a donor-printer conversion.

## Baseline

- Engine: monochrome dry electrophotographic LED page printer
- Resolution: {t.dpi} dpi
- Speed: {t.ppm} ppm Letter target
- Process speed: {calcs['process_speed_mm_s_letter']:.3f} mm/s
- LED bar: {t.led_pixels} pixels, {calcs['led_active_width_mm']:.3f} mm active width
- Line rate: {calcs['line_rate_lps_letter']:.3f} lines/s
- Line period: {calcs['line_period_us_letter']:.3f} µs
- Raw raster rate: {calcs['raw_data_rate_mbit_s']:.3f} Mbit/s at 1 bpp
- OPC drum: Ø{t.drum_diameter_mm:.1f} mm, {calcs['drum_rpm']:.3f} rpm at process speed
- Fuser: {t.nominal_fuser_surface_temp_c:.1f} °C nominal surface target, {calcs['fuser_nip_dwell_ms']:.3f} ms nip dwell
- LED shift correction: 20 MHz requires two data lanes for the 25% line-time budget; single-lane needs >30 MHz.
- HV generation correction: generated HV artifacts now retire the impossible −720 V PCR target and expose only Rev C/D charging options.
- OPC exposure energy units: Rev B uses µJ/cm², not mJ/cm².

## Rev C engineering engines

- Station map: exposure-to-development minimum feasible delay is {station_solution['exposure_to_development']['min_feasible_delay_ms']:.1f} ms
  ({station_solution['exposure_to_development']['min_feasible_separation_deg']:.1f}°). The Rev B 50 ms (11.84°) target is geometrically
  infeasible on this cartridge; the binding spec moves to the OPC:
  ≥90% latent-contrast retention at {station_solution['derived_opc_requirement']['latent_contrast_hold_ms']:.0f} ms.
- Voltage ladder: Rev A as tabled cannot print. −720 V DC on the charge roller
  produces roughly −70 to −220 V of drum surface across the plausible air-gap
  threshold band, never the −600 V the exposure and developer numbers assume.
  Rev C proposes DC-only −1180 V or AC+DC (−600 V DC + ≥1.7 kVpp) charging;
  Rev D wires those values into the generated HV table and fails if the retired
  −720 V PCR target reappears. See `v2_voltage_ladder.json`,
  `v2_hv_bias_channels.json`, and `v2_hv_consistency.json`.
- PIDC-first calibration (H1) is implemented and closes in software:
  the synthetic rig fit predicts the hidden OPC within a few volts under
  8 V probe noise and lands the −100 V latent target; see
  `v2_pidc_calibration_demo.json`.
- Every generated JSON artifact now passes a unit-plausibility lint
  (`openframe_printer/units.py`) so the Rev B mJ/µJ class of error fails the
  build instead of waiting for review.

## Rev D added gates

- HV consistency: generated HV rows are checked against the voltage ladder; the retired −720 V PCR target cannot pass.
- H8 developer-probe budget: the developer-roller-as-probe idea now has a numeric signal/noise requirement.
- Transfer impedance control: transfer bias now has a current-mode plan from a paper/nip impedance sniff instead of fixed voltage faith.

## Generated files

- `v2_design_calcs.json`: numeric engine constants and derived timing
- `v2_exposure_summary.json`: LED bar timing, payload size, and exposure sweep
- `v2_motion_events.json`: paper-path station timing and jam windows
- `v2_hv_bias_channels.json`: HV bias channel targets and current limits
- `v2_fuser_summary.json` / `v2_fuser_sim.csv`: thermal model and warm-up trace
- `v2_led_group_map.csv`: 64-pixel LED groups across the printbar
- `v2_openframe_m1_cross_section.svg`: engine side-view geometry
- `v2_process_cartridge.svg`: cartridge cross-section concept
- `v2_nozzle_math.json`: future inkjet/nozzle R&D constants
- `v2_ep_physics_summary.json`: Rev B LED clock, OPC delay, and fuser-control guardrails
- `v2_station_map.json` / `v2_station_map.csv`: Rev C solved drum station angles, real inter-station delays, derived OPC hold spec
- `v2_voltage_ladder.json`: Rev C end-to-end electrostatic ladder; Rev A charging inconsistency and both fix options
- `v2_pidc_calibration_demo.json`: Rev C PIDC-first calibration loop (H1) with automated kill criteria
- `v2_hv_consistency.json`: Rev D HV artifact/voltage-ladder consistency gate
- `v2_dev_probe_budget.json`: Rev D H8 developer-probe signal budget
- `v2_transfer_impedance_plan.json`: Rev D paper-impedance transfer-current plan

## First v2 hardware direction

The first physical rig should be a cold paper-motion rig with no toner, no fuser heat, and no HV enabled. The second rig adds the LED timing path into a photodiode capture jig. The third rig adds a potted current-limited HV module and dummy loads. The fourth rig adds a cold process cartridge. The fifth rig closes the fuser loop under redundant thermal cutoff. That sequence builds a new printer without depending on any donor machine.
""", encoding="utf-8")
    paths.append(report)
    return paths


def main() -> None:
    paths = build_report()
    print("Generated v2 report artifacts:")
    for p in paths:
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
