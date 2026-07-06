# 56. Rev G humidity, toner-charge, and media derating

Rev D added transfer impedance sniffing, but the package still treated humidity as a vague support note. Rev G promotes humidity and media class into executable print-quality gates through `openframe_printer/environment_model.py` and `out/v2_environment_derating.json`.

## Research basis

The toner-charge example is intentionally pessimistic-but-real: one model toner dropped from -80 to -57 µC/g between 20% and 80% RH, while another chemistry was RH-insensitive. Transfer prior art also changes transfer voltage with relative humidity and adds roughly 400-600 V for transparent/polymeric media versus plain paper.

## Generated findings

Using the cited humidity-sensitive toner example, the model produces this charge sweep:

```text
20% RH: -80.0 µC/g
50% RH: -68.5 µC/g
80% RH: -57.0 µC/g
80% RH charge factor vs 50% RH: 0.832
```

The generated verdict for humid plain paper is not nominal operation:

```text
humid_80rh_plain.verdict = hold_quality_print_run_pidc_dev_bias_and_transfer_sweep
```

Rev G also keeps media transfer offsets explicit:

```text
humid_80rh_plain open-loop transfer center: 1360 V
humid_80rh_film_or_label open-loop transfer center: 1860 V
film / label offset: +500 V
```

That offset is not a command to blindly run 1860 V. It is a starting center before the Rev D impedance sniff clamps current and voltage.

## RFQ implication

The toner RFQ must include Q/M versus relative-humidity data. A toner can earn a reduced calibration burden only by proving it is RH-insensitive over the requested office range. Unknown toner plus 80% RH must hold quality printing until the PIDC/developer/transfer sweep has run.

## Research anchors

- Electrophotographic process-control prior art links toner charge per mass (Q/M), toner concentration, relative humidity, development potential, and transfer efficiency, and explicitly uses RH sensing/control to stabilize density. Rev G turns that into a gate: humid operation cannot be accepted as nominal until PIDC/developer/transfer calibration proves it.
