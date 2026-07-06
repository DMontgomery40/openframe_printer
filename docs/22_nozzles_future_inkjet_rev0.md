# 22. Future inkjet/nozzle R&D branch

Inkjet is the harder branch, but the nozzle problem is mapped here so it is not hand-waved away. This is not the first printer product path. It is a future R&D path after the monochrome engine exists.

## Why inkjet is harder

The hard part is not just moving a printhead. The hard part is repeatable picoliter fluid ejection from thousands of micron-scale nozzles while preventing drying, clogging, wetting failures, satellite drops, and color/chemistry instability.

## Rev0 piezo DOD nozzle target

| Parameter | Rev0 target |
|---|---:|
| Native pitch at 600 dpi | 42.333 µm |
| Nozzle diameter | 24 µm |
| Nozzle plate thickness | 25 µm |
| Chamber length | 55 µm |
| Chamber width | 45 µm |
| Chamber height | 28 µm |
| Drop volume | 10 pL |
| Calculated spherical drop diameter | 26.7 µm |
| Drop velocity | 7 m/s |
| Max firing frequency | 12 kHz |
| Ink viscosity | 3 mPa·s |
| Surface tension | 32 mN/m |

## Calculated dimensionless checks

The generated `out/v2_nozzle_math.json` reports:

- Reynolds number around 56 for the Rev0 target.
- Weber number around 37 for the Rev0 target.

These values are in a plausible drop-on-demand exploration zone, but they do not make a production printhead. They define the first MEMS/nozzle test-chip conversation.

## OpenFrame inkjet design philosophy

If OpenFrame ever does inkjet, the printhead must be treated as a serviceable module with:

- replaceable cap station,
- replaceable wiper,
- replaceable purge pump,
- documented ink window,
- no cartridge authentication lockout,
- explicit cleaning waste path,
- user-visible clog diagnostics,
- open electrical/mechanical interface.

## Why not thermal bubble first

Thermal bubble nozzles require high-current microheaters, thin-film stacks, passivation, cavitation-resistant materials, and extremely mature fabrication. Piezo DOD is still hard, but it is the saner open R&D branch because the actuation can be separated from some of the extreme heater-stack constraints.

## First inkjet test chip

A realistic Rev0 test chip is not a full page-width head. It is:

- 16 nozzles,
- 600 dpi pitch,
- transparent or inspectable fluid path,
- external piezo driver,
- replaceable cap,
- microscope-visible drop watcher,
- controlled ink viscosity/surface tension,
- no claim of page printing.

The electrophotographic M1 is the product path. This nozzle branch is the research path.
