# 31. Rev C solved drum station map

Rev B correctly said the cartridge "cannot just say LED before developer" and
asked for an angular station map. Rev C stops asking and solves it:
`openframe_printer/station_map.py` places every process station around the
30 mm drum with real clearance math and emits `out/v2_station_map.json` /
`out/v2_station_map.csv`.

## How the solver works

- Every station is an angular occupancy on the drum. Tangent rollers use the
  exact tangent-circle solution: centers sit at `R + r` from the drum axis,
  and the minimum angle between two rollers comes from solving the triangle
  where their center distance equals `r1 + r2 + clearance`.
- Blades and the LED optical window use declared envelope half-angles
  (12 deg cleaning blade, 10 deg LED clear cone) because their geometry is a
  housing decision, not a tangent circle.
- Stations pack in process order (transfer, cleaning, charge, exposure,
  developer) at minimum separation plus a 2 deg margin, then the leftover
  ring slack is distributed by design intent: exposure-to-developer stays at
  minimum, cleaning-to-charge gets the most room.
- Angles increase in the surface-travel direction with the transfer nip
  fixed at 180 deg. The absolute orientation can be rotated to match the
  chassis; the relative geometry is the contract.

## The headline number

The minimum feasible exposure-to-development separation on Rev A geometry is
about **38 deg**, which at 62 mm/s is about **160 ms** of latent-image travel
time. The Rev B target of 50 ms (11.84 deg) is geometrically impossible: the
developer roller body (Ø16 mm, plus clearance) and the LED clear cone alone
occupy three times that angle on a 30 mm drum.

Chasing a smaller delay with a bigger drum is backwards for this design.
The correct move is to flip the requirement onto the component that owns it:

> **Derived OPC requirement (Rev C):** the selected OPC must retain at least
> 90% of its exposure contrast 240 ms after exposure (1.5x the geometric
> minimum, covering humidity and aging drift). This is measured directly on
> the H1 PIDC rig by delaying the probe read-out.

Ordinary negative-charge OPCs are used in machines with comparable
geometry-imposed delays, so this is a requirement to verify, not a reason to
panic. But it is now a number the cartridge geometry hands to the OPC
selection process, instead of a wish the geometry cannot grant.

## Solved map (Rev A dimensions, generated values)

See `out/v2_station_map.csv` for exact angles. Representative solution:

| station | angle (deg) | note |
|---|---|---|
| transfer | 180.0 | fixed, paper path under drum |
| cleaning blade | ~243 | after transfer |
| charge PCR | ~350 | near top |
| LED exposure | ~47 | after charge |
| developer | ~85 | at minimum separation from exposure |

Ring closure check: total minimum separations ~189 deg, slack ~171 deg. The
cartridge is not crowded; the binding constraint is purely the
exposure-to-developer pair.

## What invalidates this map

- Changing any roller diameter, the drum diameter, blade envelope, or LED
  cone re-runs the solver; the map is generated, never hand-edited.
- The 2 mm clearance and 2 deg margin are bare-body values. If housing
  design eats more than the distributed slack in any gap, the solver's
  minimums must be re-derived with the real envelopes.
