# 34. Rev C novel design hypotheses

Same contract as doc 29: these are OpenFrame-specific proposals, allowed to be uncited, required to be falsifiable. Each one exists because a Rev C engine or artifact makes it testable, not as decoration.

Rev D update: H8 is no longer just prose. It now has a first-order signal/noise budget in `openframe_printer/dev_probe.py`, generated output in `out/v2_dev_probe_budget.json`, and detailed acceptance logic in doc 36. H9 and H10 remain falsifiable hypotheses.

## H8: The cartridge is the instrument — developer roller as electrostatic probe

### Proposed idea

Electrostatic voltmeter probes are the priciest part of the H1 rig. But the developer roller is already a biased electrode a controlled distance from the drum, wired to a monitored HV channel (`DEV_MON`).

During a non-printing calibration rotation (developer disengaged from toner supply or run pre-toner in the cold cartridge), write a known latent pattern with the LED bar and measure the induced current/voltage disturbance on the developer bias line as the pattern passes the nip. The passing surface potential modulates the roller-drum capacitance charge; the monitor sees it.

The printer then owns a coarse PIDC measurement *in situ*, with zero added external probes: charge, expose a staircase, watch `DEV_MON`, fit the PIDC, choose pulse widths — the doc 33 loop without the lab electrostatic probe.

### Rev D status

Budgeted, not proven. The first-order model says a 64×64-pixel patch produces about 6.45 nA full-scale ideal induced current, and an 8-step staircase needs about 0.31 nA RMS monitor noise for 3σ step separation. Rev D recommends starting with 128×128-pixel patches and a true DEV_MON transimpedance/current-sense mode.

### Test

On the H1 rig, mount a developer roller at nip distance with the real bias supply. Compare the induced-signal staircase against the electrostatic probe reading for the same latent staircase. Signal correlates monotonically with probe potential and resolves 8 steps -> keep.

### Kill criteria

Reject if the induced signal is below the HV monitor’s noise floor, needs instrumentation-grade amplification that will never ship, or the bias supply cannot be made quiet enough during the measurement window.

## H9: LED bar thermal droop feed-forward from payload history

### Proposed idea

LED output droops as junction temperature rises; a dense page self-heats the bar and prints lighter at the bottom unless compensated. The controller already knows every byte it shifted. Maintain a per-64-pixel-group thermal state (exponential decay accumulator of recent on-pixel counts) and add a small pulse-width correction from a droop table.

This is feed-forward from data the controller cannot avoid having; no temperature sensor on the bar is required for the first version.

### Test

LED timing jig with a photodiode: run a solid-band page, log photodiode output versus line number and group, fit droop versus accumulated payload. Enable the correction and require the residual intensity droop over a full page to drop by at least half.

### Kill criteria

Reject if bar-to-bar droop variation exceeds the correction, or if droop is below the print-visible threshold anyway.

## H10: Per-angle drum health map from the margin strip

### Proposed idea

Doc 29’s H6 reads printed density marks with a cheap reflective sensor. The drum rotates about 3.9 times per Letter page, so density marks land at known drum angles. Accumulate H6 readings *indexed by drum angle* into a per-angle health map.

A local OPC scratch, fatigue band, or charge-roller flat shows up as a periodic density deviation locked to drum phase — distinguishable from developer or paper effects, which are not drum-periodic. The printer can then report “drum wear at 140 deg” instead of “image quality degraded,” and the open-consumables story gets a diagnostic no sealed cartridge offers.

### Test

Score a sacrificial drum deliberately. Run 50 pages of margin strips. The health map must localize the scratch angle within ±15° and separate it from an unscratched control drum.

### Kill criteria

Reject if drum-phase tracking drifts faster than the map accumulates, or if paper-position noise swamps the drum-periodic signal.

## Interaction with the Rev B hypotheses

H8 strengthens H1. H9 consumes the existing 64-pixel group map artifact. H10 upgrades H6 from scalar feedback into a spatial diagnostic. None of them create a lockout path: every measurement stays local and advisory.
