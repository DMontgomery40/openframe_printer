# 28. Research grounding Rev B: physics corrections, not prose polish

This file exists because OpenFrame cannot become real by adding nicer wording around unexamined constants. Rev B replaces several hand-waved assumptions with testable electrophotographic control variables.

## Source map

1. **OPC sensitivity and LED wavelength compatibility**  
   Fuji Electric, *Organic Photoconductors for Printers*, Fuji Electric Review, Vol. 57 No. 1, 2011.  
   Source: https://americas.fujielectric.com/files/FER-57-1-013-2011.pdf

2. **Toner layer bias controls**  
   Chiseki Yamaguchi and Manabu Takeuchi, *Properties of Toner Layer in Single Component Developing Process*, IS&T Recent Progress in Toner Technology, 1997.  
   Source: https://www.imaging.org/common/uploaded%20files/pdfs/Papers/1997/RP-0-68/2321.pdf

3. **Fuser process variables and dimensionless control groups**  
   Chih-Hung Chen and Tsai-Bou Yang, *Dimensional Analysis on Toner Fusing Process*, IS&T Recent Progress in Toner Technology, 1997.  
   Source: https://www.imaging.org/common/uploaded%20files/pdfs/Papers/1997/RP-0-68/2339.pdf

4. **Fuser apparatus control variables**  
   M. K. Tse, *A Fusing Apparatus for Toner Development and QC*, IS&T NIP 1997.  
   Source: https://www.qea.com/wp-content/uploads/2015/04/Paper_1997_IST-NIP_A_Fusing_Apparatus_for_Toner_Development_and_QC2-newaddr.pdf

## Correction 1: OPC exposure was off by a unit class

The previous package used `mJ/cm²` for OPC exposure. That is the wrong scale for ordinary OPC exposure targets.

Fuji's negative-charge OPC table gives sensitivity as exposure energy needed to discharge surface potential from -600 V to -100 V. The listed range is **0.15 to 0.80 µJ/cm²**, depending on OPC type. The same paper says these OPCs have nearly uniform sensitivity over **600-800 nm**, making them suitable for laser diode and LED exposure sources.

Rev B change:

- `exposure_energy_sweep_mJ_cm2` is replaced with `exposure_energy_sweep_uJ_cm2`.
- `initial_nominal_exposure_mJ_cm2` is replaced with `initial_nominal_exposure_uJ_cm2`.
- Docs and YAML now say **µJ/cm²**, not **mJ/cm²**.

Engineering consequence:

- The old number was plausibly **1000x too much optical exposure** if interpreted literally.
- The LED bar design must be specified by measured irradiance at the OPC, line dwell, wavelength, and surface potential response, not by a copied energy value.

## Correction 2: LED line timing had a hidden single-lane bug

A 5120-pixel, 1-bit line is 5120 bits or 640 bytes.

At 12 ppm Letter, Rev A line period is 682.796 µs.

The old generated field said the minimum clock for shifting a full line inside 25% of the line period was about 0.03 MHz. That was a unit bug. The corrected value is about **29.99 MHz for one data lane**.

Rev B keeps 20 MHz only if the bar is split across two 2560-bit data lanes:

| LED drive mode | Shift time at 20 MHz | Fraction of 682.796 µs line period | Meets 25% budget? |
|---|---:|---:|---:|
| One 5120-bit lane | 256 µs | 37.5% | no |
| Two 2560-bit lanes | 128 µs | 18.75% | yes |

Engineering consequence:

- Either use two LED data lanes as a hard requirement, or raise the single-lane clock above 30 MHz before latch/OE margin.
- The connector already had `LED_DATA0_P/N` and `LED_DATA1_P/N`; Rev B makes the second lane functional instead of decorative.

## Correction 3: exposure-to-development delay is now a first-class geometry constraint

Fuji's OPC paper says that, for small 20-30 mm OPCs in high-speed printers, exposed-area potential must stay uniform during the exposure-development time, and gives 50 ms or less as typical in such machines.

OpenFrame M1 is slower: 62.0 mm/s process speed. At this speed, a 50 ms exposure-to-development budget corresponds to only:

```text
62.0 mm/s × 0.050 s = 3.10 mm surface travel
```

For a 30 mm drum, circumference is 94.25 mm, so 3.10 mm is only **11.84 degrees** around the drum.

Engineering consequence:

- The package must not merely say "LED bar before developer." It must specify angular placement of charge, exposure, developer, transfer, and cleaning stations around the OPC.
- If the mechanical cartridge cannot place exposure and development that close, then the selected OPC must be proven stable at the real delay. That requires a PIDC/dark-decay test, not guessing.

## Correction 4: developer control needs more than one `DEV_HV` knob

Yamaguchi and Takeuchi studied a non-magnetic single-component developing unit with a developing roller, toner supply roller, and regulating blade, each tied into bias conditions. They found that toner layer mass and toner charge change with the bias relationships. They also found toner charge distribution through the layer is not uniform, and that optimized combinations of bias voltages can make the toner layer more uniformly charged.

OpenFrame's old cartridge contact layout exposed only:

- PCR HV
- developer HV
- ID sense
- ground

Rev B adds a research path for optional developer sub-biases:

- `DEV_ROLLER_BIAS`
- `DEV_BLADE_BIAS`
- `TONER_SUPPLY_BIAS`

Engineering consequence:

- The first production-ish cartridge can still collapse these internally for simplicity.
- The lab cartridge should expose them separately because background fog, density, and weak development may be unsolvable if all developer physics are hidden behind one rail.

## Correction 5: fusing is not only surface temperature

The old fuser model used heat capacity, thermal resistance, heater power, and a PID loop. That is useful for warm-up and over-temperature work, but it does not predict whether toner actually anchors to paper.

Chen and Yang's dimensional analysis treats hot-roll fusing quality as controlled by two grouped variables:

```text
K = f(Pt² / MD, T / Ta)
```

where:

- `P` = average nip pressure
- `t` = residence/dwell time
- `M` = developed toner mass per unit area
- `D` = toner particle diameter
- `T/Ta` = fuser-to-ambient absolute temperature ratio

Tse's fusing apparatus paper separately calls out dwell time, surface temperature, and pressure as critical fusing variables.

Rev B change:

- Adds `openframe_printer/ep_physics.py`.
- Adds `v2_ep_physics_summary.json`.
- Adds a relative fusing-control proxy for calibration planning.

Engineering consequence:

- The fuser test plan must sweep at least surface temperature, process speed/dwell, nip pressure, and toner mass laydown.
- Raster coverage is now valuable process data: a dense black page and a 5% text page should not be treated as physically identical loads.

## Correction 6: the correct product path is not "pick magic constants," it is "measure the response surface"

The new rule for OpenFrame calibration is:

```text
Do not tune constants directly.
Tune measured physical targets.
```

Examples:

- Do not tune LED power; tune OPC surface potential after exposure at the real exposure-to-development delay.
- Do not tune fuser temperature alone; tune rub/tape/offset results against dwell, pressure, toner mass, and temperature.
- Do not tune transfer voltage alone; tune transfer efficiency and background fog across humidity, paper weight, and transfer current.
- Do not tune developer bias alone; tune toner mass, toner charge, background fog, and density.
