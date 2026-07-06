# 29. Novel design hypotheses Rev B

These are **not** literature claims. They are proposed OpenFrame-specific mechanisms and experiments derived from the research grounding. They are deliberately allowed to be uncited because the point is to create new design ideas, not only summarize known work.

Each hypothesis has a falsification path. If it fails the test, it gets removed.

## H1: PIDC-first calibration instead of exposure-energy calibration

### Proposed idea

Treat the OPC as the controlled object, not the LED bar.

Build a small rotating OPC coupon rig with:

- the intended OPC drum or a sacrificial strip wrapped around a grounded aluminum cylinder,
- the actual LED bar or a calibrated LED segment,
- a non-contact electrostatic surface-potential probe or a guarded capacitive probe,
- a humidity/temperature sensor,
- adjustable delay between exposure and measurement.

Fit:

```text
V_surface = f(V_charge, exposure_energy, wavelength, time_after_exposure, humidity, drum_history)
```

Then the printer stores a target latent-voltage window instead of a target optical-energy value.

### Why this may be powerful

OPC suppliers can change layer stacks, toner vendors can change charge agents, and LED bars can age. A surface-potential target survives those changes better than a blind optical-energy constant.

### Test

1. Charge OPC to -600 V, -700 V, and -800 V.
2. Expose with 0.15-1.00 µJ/cm² at 780 nm or the actual LED wavelength.
3. Measure surface potential after 25, 50, 100, and 200 ms.
4. Repeat at low, normal, and high humidity.
5. Fit a lookup table and use it to choose LED pulse width.

### Kill criteria

Reject if the probe noise, drum runout, or environmental drift is too large to predict density better than a simple fixed LED sweep.

## H2: Exposure-to-development geometry lock

### Proposed idea

The process cartridge gets a hard angular station map, not just component names.

For Rev B, define:

```text
charge_angle_deg
exposure_angle_deg
developer_angle_deg
transfer_angle_deg
cleaning_angle_deg
```

The critical value is:

```text
exposure_to_development_delay_ms = drum_arc(exposure_angle, developer_angle) / process_speed
```

At 62 mm/s, even a 10 mm arc is 161 ms, so the design must either compress the exposure/developer spacing or select/prove an OPC that tolerates the actual delay.

### Test

Make three cartridge side plates with different LED-to-developer angular spacing:

- tight: about 12 degrees,
- medium: about 25 degrees,
- relaxed: about 40 degrees.

Use the same charge, exposure, developer, toner, paper, and fuser settings. Compare density, edge acuity, ghosting, and background fog.

### Kill criteria

Reject any geometry whose density or line acuity collapses after the delay even if exposure energy is increased.

## H3: Developer blade bias as an open calibration rail

### Proposed idea

Expose a developer regulating-blade bias rail in the lab cartridge.

Most consumer printers hide developer physics inside proprietary cartridges. OpenFrame should expose a research cartridge where the blade can be biased separately from the developer roller. The user-facing product can later simplify this, but the lab platform should not throw away the variable before understanding it.

### Test

Sweep:

```text
DEV_ROLLER_BIAS = -150 to -500 V
DEV_BLADE_BIAS = DEV_ROLLER_BIAS -300 V to DEV_ROLLER_BIAS +300 V
mechanical doctor gap = 80 to 180 µm
```

Measure:

- solid density,
- background fog,
- toner mass on paper,
- toner mass remaining on drum,
- developer roller filming,
- page-to-page stability.

### Kill criteria

Do not keep the rail if it cannot improve density/fog stability enough to justify added HV contacts and safety burden.

## H4: Page-specific fuser control from raster coverage

### Proposed idea

Use the rasterizer to estimate toner mass before the sheet reaches the fuser.

The fuser controller gets a per-page load estimate:

```text
M_page ≈ dense_black_laydown_mg_cm2 × printed_area_cm2 × coverage_fraction
```

Then it chooses a control point from a calibration map:

```text
surface_temp, speed, nip_pressure_class = f(M_page, paper_weight, ambient, previous_pages)
```

This is not only energy-saving. It should reduce cold offset on dense pages and reduce excessive gloss/curl on light pages.

### Test

Print a controlled set:

- 5% text page,
- 20% graphics page,
- 50% halftone page,
- 100% solid patch page,
- alternating dense/light pages.

For each, sweep fuser temperature and process speed. Measure rub resistance, tape pull, offset to hot roller, curl, and gloss.

### Kill criteria

Reject adaptive fusing if it causes visible page-to-page inconsistency or makes first-page timing too complex for Rev B.

## H5: Transfer-bias paper impedance sniff

### Proposed idea

Use the leading margin of each sheet as a harmless transfer test zone.

Before the image reaches the transfer nip, apply a low-current transfer-bias ramp and measure current through the paper/transfer path. Use that current signature as a rough paper/humidity/thickness proxy. Then pick the transfer bias for the actual image area.

### Why this may matter

Paper is not a passive ideal receiver. Paper weight, moisture, coating, and thickness alter transfer fields. A printer with no expensive media sensor might still infer enough from transfer current to avoid weak transfer or background problems.

### Test

Use 60, 75, 90, and 105 gsm paper at low/normal/high humidity. Record transfer current during a low-energy pre-image ramp. Compare current features with the transfer voltage that gives the best density and lowest background.

### Kill criteria

Reject if the current signature does not separate paper states better than a simple user-selected media type.

## H6: Margin-strip self-calibration without DRM

### Proposed idea

Print tiny calibration marks in a sacrificial margin or startup sheet, then read them with a cheap reflective sensor in the paper path. The marks are not authentication marks and are not cartridge lockouts. They are density feedback.

Use them to update:

- LED exposure correction,
- developer bias,
- transfer bias,
- fuser control point.

### Test

Install a low-cost reflective optical sensor after fusing. Print a page edge strip with known density steps. Compare sensor response with flatbed-scan density and rub/tape results.

### Kill criteria

Reject if sensor contamination, paper color variation, or toner gloss makes feedback unreliable.

## H7: Open consumables fingerprinting for advice only

### Proposed idea

Measure consumable behavior instead of authenticating consumable identity.

The printer can build a local profile:

```text
toner_profile = observed_density_response + fog_response + fuser_response + transfer_response
```

It can warn:

```text
"This toner needs higher fuser energy" or "This cartridge has high background fog."
```

It must not say:

```text
"Unauthorized cartridge. Printing blocked."
```

### Test

Run two or three black toner formulations through the same lab cartridge. See whether the calibration system can classify behavior well enough to recommend settings.

### Kill criteria

Reject any path that drifts toward consumable lockout or requires private vendor IDs.
