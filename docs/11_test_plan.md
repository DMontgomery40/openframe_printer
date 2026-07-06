# Test plan

## Phase A: software and timing

| Test | Pass condition |
|---|---|
| Raster demo | generates valid PBM page |
| Engine math | process speed, drum rpm, line rate calculated |
| OFP1 job plan | page line count and timing exported |
| Line streaming simulation | no buffer underrun at 12 ppm equivalent |

## Phase B: cold paper path

No fuser heat, no HV, no toner, no exposure.

| Test | Pass condition |
|---|---|
| Single-sheet feed | reaches exit sensor without jam |
| 100-sheet feed | 0 jams, 0 double-feeds |
| Registration timing | repeatability within +/- 1 mm |
| Skew | <= 1 mm across width |
| Door open | motors stop, hazardous enables false |

## Phase C: thermal-only fuser bench

No paper or toner at first.

| Test | Pass condition |
|---|---|
| Warm-up | reaches 175 C target under time target |
| Control stability | maintains target without overshoot beyond warning threshold |
| Fault cutoff | heater disabled at configured fault threshold |
| Thermal fuse validation | independent cutoff path verified with safe test method |

## Phase D: process module characterization

Only with appropriate safety review.

| Test | Pass condition |
|---|---|
| Charge uniformity | target surface behavior repeatable |
| Developer bias sweep | visible density response without runaway backgrounding |
| Transfer sweep | toner transfers to paper consistently |
| Fuser sweep | adhesion acceptable without scorching |
| 100-page print | no unsafe temp drift, no repeated jams |

## Phase E: serviceability

| Test | Pass condition |
|---|---|
| Replace pickup roller | novice can do under 5 minutes |
| Replace process module | user can do without tools |
| Replace fuser module | technician can do under 15 minutes |
| Clear jam | paper path visible and reachable |
| Read logs | fault explains failed subsystem and next action |
