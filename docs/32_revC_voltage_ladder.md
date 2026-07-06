# 32. Rev C/D electrostatic voltage ladder — and the Rev A charging fault

`openframe_printer/voltage_ladder.py` connects the numbers the package already carried but never checked against each other: PCR bias, charged surface potential, exposure discharge, and developer bias. The output is `out/v2_voltage_ladder.json`.

## The fault

Rev A tables `PCR_CHARGE = -720 V` (DC) while every exposure and developer number in the package assumes a **−600 V charged drum** (the whole “0.15–0.80 µJ/cm² discharges −600 V to −100 V” story).

A DC-biased contact charge roller does not simply copy its bias to the drum. Charging happens by air-gap discharge, which begins only above a threshold voltage; above it the surface potential tracks applied bias minus that threshold:

```text
V_surface ≈ V_applied − V_th        magnitudes; V_th modeled as 500–650 V
```

With −720 V applied, the drum reaches roughly **−70 to −220 V** across the plausible threshold band. The developer bias (−320 V) is then more negative than the unexposed drum surface: the background field points the wrong way, negative toner develops onto background everywhere, and the machine prints a black page with no image contrast. Rev A as tabled cannot print.

This survived the original design pass and Rev B because no artifact computed the rungs of the ladder in one place.

## Rev C fix options, Rev D generated enforcement

Rev C proposed the two charging fixes. Rev D makes them generated artifacts and hard checks.

Active files:

- `hardware/ofp_m1_revD_hv_bias_channels.csv`
- `out/v2_hv_bias_channels.json`
- `out/v2_hv_consistency.json`

### Option A — DC-only, raised bias

`PCR_CHARGE = −1180 V` nominal, range −900 to −1400 V. Ladder check across the V_th band: charged surface −530 to −680 V, latent image around −95 to −106 V at 0.45 µJ/cm², development contrast above the first-build floor, and fog margin above the first-build floor. Every rung passes, but the surface potential tracks V_th drift from humidity and roller aging.

This is a supply redesign: Rev A’s channel maxed at −900 V.

### Option B — AC+DC

DC component −600 V with a Rev D AC component of **1.7 kVpp** at roughly 1–2 kHz. The modeled physics floor across the threshold band is 1.3 kVpp; 1.7 kVpp is the build spec with headroom. The alternating discharge converges the surface to the DC value, so charging depends less on threshold drift. The cost is an AC HV stage plus charge-noise and wear characterization.

The developer bias (−320 V) survives the voltage ladder if the charged surface is actually around −600 V. It does **not** survive the original −720 V PCR error.

## New Rev D build gate

`hv_consistency_summary()` catches artifact drift. It fails if:

- a generated PCR row returns to nominal −720 V;
- Option A no longer matches the ladder’s −1180 V DC;
- Option B no longer matches −600 V DC;
- Option B’s AC amplitude falls below the ladder physics floor;
- Option B’s generated AC value stops matching the Rev D 1.7 kVpp spec.

Run:

```bash
python3 -m openframe_printer.design_report && python3 scripts/smoke_test.py && python3 scripts/model_tests.py
```

## Boundary between model and measurement

Everything here is the standard DC contact-charging approximation plus the package’s PIDC model, with V_th treated as an uncertainty band rather than a constant. The H1 coupon rig replaces the model numbers with measured ones; the ladder structure — and the requirement that all rungs be checked together — stays. The point of the ladder is self-consistency: it rejects designs whose own numbers cannot coexist.

## Research anchors

- Roller charging proceeds by air-gap breakdown between the biased roller and photoreceptor: `https://www.qea.com/wp-content/uploads/2015/04/Paper_1997_IST-NIP_On-Roller-Charging-of-Photoreceptors-for-Electrophotography2-newaddr.pdf`
- AC+DC contact charging converges the surface potential toward the DC bias after the AC component exceeds the discharge-start threshold: `https://patents.google.com/patent/US7764888B2/en`
- Fuji OPC sensitivity data uses µJ/cm² exposure units, not mJ/cm²: `https://americas.fujielectric.com/files/FER-57-1-013-2011.pdf`
