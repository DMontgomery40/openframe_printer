# 36. Rev D H8 developer-probe signal budget

H8 proposed using the developer roller as an in-situ electrostatic probe. Rev D turns that into a first-order signal budget in `openframe_printer/dev_probe.py`, emitted as `out/v2_dev_probe_budget.json`.

This is not a proof that H8 works. It is the first real filter: if the induced signal is too small or the monitor noise is too high, kill the idea before it infects the firmware plan.

## Model

Treat the developer/drum region over one calibration patch as a small capacitance:

```text
C = ε0 * εr * A / gap
Q = C * ΔV
I = Q / transit_time
```

Default Rev D assumptions:

| Parameter | Value |
|---|---:|
| Patch | 64 × 64 pixels at 600 dpi |
| Patch width/process length | 2.709 mm |
| Developer/drum gap used for budget | 150 µm |
| Effective dielectric constant | 1.3 |
| Latent voltage span | 500 V |
| Process speed | 62 mm/s |

Default output:

| Quantity | Result |
|---|---:|
| Patch capacitance | 0.563 pF |
| Induced charge over 500 V span | 0.282 nC |
| Patch transit time | 43.699 ms |
| Full-scale ideal current | 6.445 nA |
| 8-step current spacing | 0.921 nA |
| Required monitor noise for 3σ step resolution | 0.307 nA RMS |

## Rev D verdict

A generic HV voltage monitor is not enough to assume H8 works. The signal is in the nanoamp range. The first realistic hardware path is a guarded DEV_MON transimpedance/current-sense mode and larger calibration patches.

For a 0.5 nA RMS DEV_MON noise target, Rev D recommends 128×128-pixel patches. That doubles the ideal full-scale current to about 12.89 nA and gives about 1.84 nA step spacing for an 8-step staircase.

## Test

1. Use the H1 coupon rig with an external electrostatic probe as ground truth.
2. Install the developer roller at the intended gap, initially with no toner feed.
3. Write an 8-step latent staircase.
4. Capture developer induced current through the guarded DEV_MON path.
5. Fit the same PIDC model from doc 33 using the developer signal instead of the external probe.

## Pass/fail

Pass:

- The induced staircase is monotonic.
- Step separation is at least 3σ with the measured DEV_MON noise.
- The fitted PIDC predicts external-probe holdout readings within 25 V.
- The measurement does not disturb developer bias enough to alter the latent image.

Fail:

- Current signal is below the practical monitor floor.
- Toner installation destroys monotonicity.
- Measurement requires external lab equipment that cannot become part of the printer.
- Developer bias ripple or TIA switching creates fog or density artifacts.

## Novel content boundary

The capacitance/current math is elementary electrostatics. The OpenFrame-specific novelty is using the existing developer roller and bias monitor as a local PIDC sensor, then proving or killing it with a quantified signal budget.

## Research anchor

Developer quality depends on OPC charged/discharged level, toner charge, and developer/magnetic roller bias; that makes the developer roller an electrically meaningful station rather than a passive mechanical part: `https://www.qea.com/wp-content/uploads/2015/04/Paper_1997_IST-NIP_Magnetic-Properties-of-Magnetic-Rollers2-newaddr.pdf`
