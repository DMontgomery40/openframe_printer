# 38. Rev D new hypotheses

These are novel-but-testable OpenFrame proposals created after Rev D made the HV ladder, developer-probe budget, and transfer impedance plan executable. They are not cited as established printer practice. Each has a concrete kill path.

## H11: DEV_MON dual-mode — bias readback during print, TIA probe during calibration

### Proposed idea

Do not add a separate electrostatic voltmeter. Give `DEV_MON` two modes:

1. **Print mode:** ordinary scaled developer-bias voltage/current readback.
2. **Calibration mode:** a guarded transimpedance amplifier path that measures nanoamp induced current from latent patches passing the developer roller.

The mode switch is hardware-gated so calibration mode cannot be active during customer printing unless firmware explicitly enters a non-printing calibration cycle.

### Why it is new here

H8 was a concept. Rev D's budget shows the signal is nanoamp-scale and names the missing hardware requirement. H11 turns that into a specific analog architecture requirement.

### Test

Build a DEV_MON boardlet with selectable voltage-monitor and TIA ranges. Feed known capacitively coupled nanoamp test pulses, then repeat with the H1 latent staircase.

### Kill criteria

Reject if the switching network injects enough charge to disturb the developer bias, if the TIA cannot survive HV transients, or if production shielding/guarding makes the cost worse than a cheap dedicated sensor.

## H12: Density-aware transfer waveform shaping from raster coverage

### Proposed idea

The controller already knows upcoming raster coverage before the sheet reaches the transfer nip. Use per-line or per-band coverage to bias the transfer current slightly ahead of high-toner-mass regions, within the transfer impedance control envelope.

This is not a license to overdrive transfer. It is a bounded correction layered on top of H5/Rev D impedance sniffing.

### Test

Print alternating high-coverage and low-coverage bands on the transfer rig. Compare constant transfer current against bounded density-aware current shaping. Keep only if optical density uniformity improves without raising background fog or edge scatter.

### Kill criteria

Reject if correction depends too strongly on paper type, if it creates haloing at coverage transitions, or if current shaping hides rather than fixes a poor transfer roller/mechanics choice.

## H13: Sacrificial non-image impedance strip for paper classification

### Proposed idea

Before image transfer begins, run a short non-image leading strip through the transfer nip and inject a safe diagnostic current pulse. Estimate paper/nip impedance without marking the image area. Use that one measurement to select transfer current, fuser preheat offset, and whether to slow/reject extreme paper.

### Test

Run the same paper stock across humidity conditioning. The strip-derived impedance should predict transfer success/failure better than tray settings alone.

### Kill criteria

Reject if the strip risks visible marks, if the measurement is not repeatable with sheet position, or if the extra leading margin destroys printable area expectations.

## H14: PCR option auto-characterization before committing to hardware

### Proposed idea

Build a dual-capable HV bench module with both raised-DC and AC+DC PCR charging. On the same drum/coupon, compare charge uniformity, dark decay, acoustic/electrical noise, ozone/odor proxy, and roller wear over accelerated cycles. Pick Option A or B from measurements, not preference.

### Test

Run the H1 coupon rig with both charge modes across humidity and temperature. Measure charged surface uniformity, latent target accuracy, and short-term drift.

### Kill criteria

Reject Option A if threshold drift breaks charge uniformity. Reject Option B if AC artifacts, noise, or wear exceed the benefit of threshold immunity.
