# 47. Rev F: LED thermal feed-forward

Engine: `openframe_printer/led_thermal.py`. Artifact: `out/v2_led_thermal_feedforward.json`.

## Finding

H9 was previously a hypothesis: use the payload already shifted to the LED bar to predict thermal droop. Rev F implements the first-order version.

For each 64-pixel LED group, the model computes:

```text
payload coverage -> line duty -> group temperature rise -> relative optical output -> pulse compensation
```

The output is bounded by an 8% pulse-compensation cap and is still subordinate to the photodiode/PIDC rig. It is a feed-forward prior, not a final calibration.

## Generated result

With the current conservative model:

| Case | Max group temperature rise | Worst raw output | Worst latent error before comp | Worst latent error after comp |
|---|---:|---:|---:|---:|
| Office 5% uniform | ~0.16 °C | 0.9995 | ~0.05 V | ~0 V |
| Left half black | ~3.15 °C | 0.9906 | ~1.0 V | ~0 V |
| Center black bar | ~3.15 °C | 0.9906 | ~1.0 V | ~0 V |
| Solid black page | ~3.15 °C | 0.9906 | ~1.0 V | ~0 V |

The voltage error is small in this first-order model, which is a useful result: H9 is not a substitute for H1/PIDC. Its value is in reducing group-to-group density drift before the real sensor loop trims it.

## Research grounding

LED output depends on junction temperature, and LED print heads/EP image-forming systems have prior art around temperature compensation and LED-head thermal effects:

- `https://www.onsemi.com/pub/collateral/tnd328-d.pdf`
- `https://patents.google.com/patent/US5177500`
- `https://data.epo.org/publication-server/rest/v1.0/publication-dates/19950830/patents/EP0479157NWB1/document.pdf`
- `https://www.oki.com/global/technologies/otr/assets_c/uploads/otr-222-R08.pdf`

## Enforced in code

Model tests require:

- black payload groups heat more than blank groups,
- compensation remains capped,
- the predicted latent-voltage error is reduced below 0.1 V in the first-order model.
