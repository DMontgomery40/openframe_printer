# 33. Rev C PIDC-first calibration — H1 implemented

Rev B's H1 proposed treating the OPC, not the LED bar, as the controlled
object: store a target latent-voltage window and choose LED energy to land
in it. Rev C ships that as running code in `openframe_printer/pidc_model.py`
with the demonstration artifact `out/v2_pidc_calibration_demo.json`.

## What exists now

1. **PIDC model.** Saturating exponential discharge
   `V(E) = V_r + (V_0 - V_r) * exp(-E / E_a)` — an engineering interpolant
   for rig data, anchored to the Fuji negative-charge OPC window
   (0.15-0.80 uJ/cm^2 for -600 V to -100 V). Analytic inverse for
   "what exposure reaches this voltage".
2. **Fitter.** Dependency-free least squares (grid + coordinate refinement)
   that recovers `(V_r, E_a)` from noisy probe measurements. A coupon rig
   produces tens of points; fit cost is irrelevant.
3. **Pulse chooser.** The firmware-facing inversion: target latent voltage
   plus measured LED irradiance at the drum gives a pulse width, checked
   against the line-period duty budget. At 15 mW/cm^2 and the nominal
   0.45 uJ/cm^2 OPC, the pulse is ~34 us in a 683 us line — 5% duty,
   comfortable next to the two-lane shift timing.
4. **Synthetic rig with automated kill criteria.** A hidden "true" OPC the
   fitter never sees generates noisy readings (8 V sigma, 8 energies x 3
   repeats). The loop closes: prediction error < 3 V against truth, chosen
   pulse lands the -100 V target within ~2 V, and both sit far inside the
   H1 kill limits (25 V / 30 V). Cranking the noise to hopeless levels
   (250 V sigma) fails the criteria — the scoring is honest, not
   decorative. `scripts/model_tests.py` pins both behaviors.

## The calibration contract

The stored calibration is a **latent-voltage window**, not an optical
energy:

```text
target: V_latent = -100 V +/- 30 V at the developer nip
inputs: fitted PIDC (V_r, E_a), measured LED irradiance, line period
output: per-line LED pulse width (optionally per 64-pixel group)
```

The station map (doc 31) contributes the delay at which the window must
still hold: >= 90% contrast retention at 240 ms, measured by delaying the
rig's probe read-out. The voltage ladder (doc 32) contributes the charged
surface the discharge starts from. The three artifacts are one system.

## From synthetic to physical

The physical H1 rig replaces `synthetic_rig_demo`'s reading generator with
an electrostatic probe; the fitter, pulse chooser, scoring, and kill
criteria are unchanged. The software answers the question a rig cannot:
the loop *would* close if the probe beats 8 V sigma — so probe selection
now has a numeric requirement instead of a hope.
