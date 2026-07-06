# 48. Rev F: new falsifiable hypotheses

These are intentionally not written as established facts. They are novel OpenFrame-specific design bets produced by connecting the Rev F executable models.

## H11 — adaptive minimum-dot unlock after measured dot survival

Rev F clips below 4/64 because the first engine cannot assume single-pixel EP stability. After H1/PIDC and the developer rig measure dot survival across humidity, drum age, and toner charge, the rasterizer can unlock smaller seeds only in operating regions where the measured survival probability clears a threshold.

Pass/fail: print 1×1, 1×2, 2×1, and 2×2 dot fields at multiple developer biases and humidities. Unlock a feature size only if optical density and missing-dot rate stay inside a measured limit for at least 500 pages of accelerated drum cycling.

## H12 — interlock common-cause self-diagnosis without relying on it for safety

Topology C does not rely on firmware, but firmware can still diagnose aging. Every door-open event should produce a chain-A/chain-B/energy-separator transition signature. Missing transitions become a service warning before the second fault appears.

Pass/fail: inject stuck contacts and common actuator faults. The hardware must stay safe without firmware; firmware must still identify the fault class from transition signatures in at least 95% of injected cases.

## H13 — fuser media inference from thermal droop

The fuser-power model says media mass and moisture materially change load. During the first 10 sheets of a job, estimate media class from heater duty and thermistor droop while holding process speed. Use the estimate to choose speed/temperature before jams or poor fixing appear.

Pass/fail: run 60/75/90/120 gsm sheets at dry/nominal/damp conditions. Classifier must separate light/normal/heavy or recommend safe slow mode before the fourth sheet.

## H14 — LED payload thermal prior fused with PIDC residuals

H9 predicts group-level optical droop from raster coverage. H1/PIDC observes latent voltage after exposure. Fuse them: use H9 as the prior and PIDC as the correction. The residual map then separates LED thermal behavior from OPC sensitivity drift.

Pass/fail: intentionally heat half the LED bar and age one OPC sector. The fused model must attribute thermal droop to LED groups and persistent residual error to drum angle, not smear both into one scalar density correction.

## H15 — toner gauge correction from transfer/waste current

Rev E's pixel-count toner gauge assumes a transfer efficiency. Rev D's transfer model measures paper/nip impedance and transfer current. Use transfer current residuals and waste-bin growth to correct the pixel gauge without a cartridge chip.

Pass/fail: run matched coverage pages on normal and high-impedance media. The corrected gauge must estimate remaining usable toner more accurately than raw pixel count over at least one 80 g cartridge equivalent, while never locking out printing.
