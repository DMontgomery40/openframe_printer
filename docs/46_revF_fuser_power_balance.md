# 46. Rev F: fuser continuous paper-load balance

Engine: `openframe_printer/fuser_power.py`. Artifact: `out/v2_fuser_power_balance.json`.

## Finding

The existing fuser model is a warm-up/free-air model. It proves the roller can heat without overshoot; it does **not** prove 12 ppm print-throughput, because it never charges the heater for the paper, moisture, and toner moving through the nip.

Rev F adds that missing energy path.

## First-order balance

With the existing fuser constants:

```text
heater power: 800 W
surface target: 178 °C
ambient: 25 °C
thermal resistance: 0.235 °C/W
```

Idle/environment loss at target is:

```text
(178 - 25) / 0.235 = 651 W
```

That leaves only about **149 W** for media before any steady reserve. At 12 ppm Letter, nominal 75 gsm media consumes about **134 W** in the Rev F model, leaving only **14 W** spare. A 10% heater reserve would require 80 W spare, so nominal media fails the first-build steady-margin gate.

| Case | Media load | Remaining margin | 10% reserve pass? | Required heater |
|---|---:|---:|---:|---:|
| 75 gsm nominal plain | ~134 W | ~14 W | no | ~866 W |
| 90 gsm damp heavy | ~211 W | negative | no | ~942 W |
| 60 gsm dry light | ~92 W | ~57 W | no | ~823 W |

## Engineering consequence

Do not claim 12 ppm on plain paper from the warm-up curve alone. Before the combined print rig, choose one:

1. improve fuser insulation above the current 0.235 °C/W assumption,
2. raise heater power and re-run safety/thermal cutoff design,
3. firmware-limit heavy/damp media speed,
4. choose lower-energy toner with a measured fusing latitude.

## Research grounding

Fusing quality is governed by heat, pressure, dwell/process speed, media, and toner properties — not surface temperature alone:

- `https://www.qea.com/wp-content/uploads/2015/04/Paper_1997_IST-NIP_A_Fusing_Apparatus_for_Toner_Development_and_QC2-newaddr.pdf`
- `https://www.imaging.org/common/uploaded%20files/pdfs/Papers/1997/RP-0-68/2339.pdf`
- `https://ippta.co/wp-content/uploads/2021/01/IPPTA-CI-2003-133-138-Electrophotography-Effects-of.pdf`

Paper heat and moisture transport through the fuser are real paper-path quality/jam variables, not trivia:

- `https://www.researchgate.net/publication/317773479_Moisture_transport_in_paper_passing_through_the_fuser_nip_of_a_laser_printer`
- `https://www.jstage.jst.go.jp/article/isj/52/6/52_567/_pdf`

## Enforced in code

Model tests require nominal 75 gsm to fail the steady reserve with the current fuser constants and require damp/heavy media to call for power, insulation, or speed limiting.
