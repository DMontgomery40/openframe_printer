# 35. Rev D HV generation consistency gate

Rev C correctly found the major electrostatic fault: the original −720 V DC primary-charge target cannot charge the drum to the −600 V surface potential assumed by the exposure and developer model. But Rev C still allowed a subtler engineering failure: the generated HV JSON and smoke test could remain stale while the prose and CSV said the issue was fixed.

Rev D makes that impossible to miss.

## What changed

`openframe_printer/hv_model.py` now generates the active HV table directly:

| Channel | Option | Nominal | Range | AC |
|---|---|---:|---:|---:|
| PCR_CHARGE | A_dc_only | −1180 V | −900 to −1400 V | none |
| PCR_CHARGE | B_ac_dc | −600 V DC | −450 to −750 V DC | 1.7 kVpp |
| DEVELOPER_BIAS | selected | −320 V | −150 to −500 V | none |
| TRANSFER_ROLLER | selected_current_limited | +1600 V target | +700 to +2500 V | none |

The old −720 V PCR value remains in historical Rev A files only. It is now marked as `RETIRED_PCR_NOMINAL_V` in code.

## The new gate

`hv_consistency_summary()` compares the generated HV table to the voltage ladder and emits `out/v2_hv_consistency.json`.

Checks:

- `retired_rev_a_pcr_bias_absent`
- `option_a_nominal_matches_ladder`
- `option_b_dc_matches_ladder`
- `option_b_ac_spec_exceeds_physics_min`
- `option_b_ac_spec_matches_ladder_headroom`

`smoke_test.py` requires every check to pass.

## Why this matters

Printer design packages fail when documents, generator code, RFQs, and test scripts carry different truths. Rev C found a physics bug; Rev D prevents the same class of bug from surviving as stale generated output. The HV supply is now ordered from generated data, not from an outdated table buried in a doc.

## Verification command

```bash
python3 -m openframe_printer.design_report && python3 scripts/smoke_test.py && python3 scripts/model_tests.py
```

## Research anchors

- Contact roller charging occurs through air-gap discharge rather than ideal voltage copying: `https://www.qea.com/wp-content/uploads/2015/04/Paper_1997_IST-NIP_On-Roller-Charging-of-Photoreceptors-for-Electrophotography2-newaddr.pdf`
- AC+DC roller charging practice and convergence toward the DC charging value: `https://patents.google.com/patent/US7764888B2/en`
