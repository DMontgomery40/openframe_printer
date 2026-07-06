# 53. Rev G new falsifiable hypotheses

These are intentionally not all cited. They are new OpenFrame-specific design hypotheses generated from the executable gaps found in Rev G. Each one has a measurement that can kill it.

## H11 — Clutch-start spool proof

Hypothesis: a low-cost printer can avoid large mandatory page RAM if the firmware refuses to start paper motion until the OFP1 decoded-line ring has enough measured margin for the current transport mode.

Test: inject deterministic host pauses into OFP1 loopback while the cold rig runs at 8, 10, and 12 ppm. Kill H11 if a mathematically passing buffer state still underruns, or if the required prefill makes first-page latency unacceptable.

## H12 — Encoder-derived drum health map

Hypothesis: the drum encoder residuals, after subtracting commanded velocity, can reveal mechanical eccentricity, gear tooth defects, or drag changes before visible banding appears.

Test: log encoder phase residuals during blank runs and correlate with printed 1D banding spectra. Kill H12 if residual peaks do not predict visible artifacts better than page-count age.

## H13 — Cheap slanted-edge LED MTF acceptance

Hypothesis: the first optical MTF acceptance test can be done without a lab-grade drum scanner by printing a slanted-edge latent/toner pattern, imaging it with a fixed macro camera, and estimating MTF50/MTF at 12 lp/mm.

Test: compare macro-camera estimates against a known-good scanner or microscope for at least three spot widths / supplier bars. Kill H13 if repeatability is worse than ±0.05 MTF at 12 lp/mm.

## H14 — Thermal-cutoff trip telemetry without defeating safety

Hypothesis: the controller can detect thermostat/fuse loop state transitions through optically isolated sense inputs without adding any series element that compromises the cutoff path.

Test: fault-inject thermostat open, fuse open, SSR welded, and thermistor stuck-cold states. Kill H14 if sensing changes the trip current/temperature behavior or can backfeed the heater.

## H15 — Transport-mode aware ppm scheduler

Hypothesis: OpenFrame can expose transport mode honestly to the user: USB HS jobs run at 12 ppm, USB FS jobs start at 8 ppm unless pre-spooled, and the host UI reports the exact reason rather than hiding it as “processing.”

Test: measure first-page-out and underrun rate across sparse, office, and solid pages. Kill H15 if users see unexplained delays or if compression-dependent speed changes cause worse perceived reliability than fixed slow mode.

## H16 — Ghost-strip erase health check

Hypothesis: a non-image margin impulse strip can track erase/quench health over time by measuring one-circumference ghost residuals, without adding a dedicated optical drum sensor.

Test: print an impulse strip at controlled density, scan one drum circumference downstream, and trend residual contrast versus erase LED current and OPC age. Kill H16 if scanner noise, paper variation, or toner scatter swamps a 1% ghost signal.

## H17 — Bleed-decay self-test as a service predictor

Hypothesis: the HV monitor ADC can measure post-disable decay constants well enough to flag an open bleeder or rising output capacitance before a service hazard appears.

Test: trip HV into dummy loads, fit decay curves for every output node, then physically open one bleeder in the potted jig. Kill H17 if fitted time constants cannot distinguish a single open bleeder from normal tolerance and ADC noise.

## H18 — Humidity-driven calibration policy beats fixed density tables

Hypothesis: a cheap RH sensor plus PIDC/developer/transfer sweep can reduce first-page density failures under 20–80% RH more effectively than a larger static lookup table.

Test: run the same toner/paper set at 20%, 50%, and 80% RH. Kill H18 if the RH-triggered sweep does not reduce density error and background fog versus fixed nominal settings.

## H19 — Output-tray capture matters more than fan-filter rating

Hypothesis: fuser/exit geometry and output-tray capture dominate emitted-particle containment more than the nominal filter rating installed on a chassis fan.

Test: measure particle counts around the fuser outlet, fan outlet, and output tray while toggling fan-only filtration versus source-plus-exit capture. Kill H19 if output-tray capture does not measurably change the high-emitter case.

## H20 — Edge-slack-aware printable-width negotiation

Hypothesis: users will prefer an honest "full width requires precise registration / reduced speed" mode over silent clipping or edge artifacts from pretending the 5120-pixel bar has 1 mm slack.

Test: expose three host modes: full-width precision, safe 214 mm imageable width, and experimental raw 5120. Kill H20 if safe-width mode creates unacceptable workflow friction compared with the hardware cost of a 5184-pixel bar.
