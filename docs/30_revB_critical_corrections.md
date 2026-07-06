# 30. Rev B critical corrections

This is the short version of the actual iteration.

## Changed from Rev A/v2

1. **OPC exposure units corrected**
   - Old: `mJ/cm²`
   - New: `µJ/cm²`
   - Reason: OPC sensitivity sources are in microjoules per square centimeter for discharge targets.

2. **LED shift-clock math corrected**
   - Old generated value: ~0.03 MHz minimum for 25% line-time shift.
   - New generated value: ~29.99 MHz for a single 5120-bit lane.
   - New design rule: 20 MHz is acceptable only with two 2560-bit lanes.

3. **Exposure-to-development delay added**
   - At 62.0 mm/s, 50 ms equals 3.10 mm of drum surface travel.
   - On a 30 mm drum that is 11.84 degrees.
   - The cartridge now needs an angular station map, not only a cross-section sketch.

4. **Developer control expanded conceptually**
   - `DEV_HV` alone is likely not enough for a real lab cartridge.
   - Rev B proposes optional `DEV_BLADE_BIAS` and `TONER_SUPPLY_BIAS` research rails.

5. **Fuser model expanded conceptually**
   - Warm-up PID remains useful.
   - Actual adhesion calibration must include dwell, pressure, toner mass, particle diameter, temperature, and paper response.

6. **Novel hypotheses separated from cited facts**
   - Known physics is in `docs/28_research_grounding_revB.md`.
   - New proposed mechanisms are in `docs/29_novel_design_hypotheses_revB.md`.
   - The novel file is intentionally not limited to citations.

## New/modified files

```text
openframe_printer/ep_physics.py
openframe_printer/exposure_model.py
openframe_printer/design_report.py
scripts/smoke_test.py
docs/18_led_exposure_bar_spec.md
docs/28_research_grounding_revB.md
docs/29_novel_design_hypotheses_revB.md
docs/30_revB_critical_corrections.md
hardware/design_targets_revA.yaml
hardware/ofp_m1_revB_lab_developer_bias_options.csv
```

## New generated output

```text
out/v2_ep_physics_summary.json
```
