# 57. Rev G emissions containment budget

OpenFrame cannot be literally open around the fuser, paper exit, toner, and fan path and still pretend emissions are someone else's problem. Rev G adds an engineering containment gate in `openframe_printer/emissions_model.py` and `out/v2_emissions_containment.json`.

This is **not** a health certification and does not replace lab measurement. It is a design gate that prevents a chassis with no capture path from being called build-ready.

## Research basis

Published laser-printer emissions literature reports particle emission rates spanning roughly 10^8 to 10^12 particles per minute. Practical safety guidance also warns that filters attached only to fan vents miss other openings, and paper output trays are often an important particle source.

## Generated cases

```text
low emitter, uncontained:             5.0e7 particles/m³, passes internal review threshold
high emitter, uncontained:            5.0e11 particles/m³, fails
high emitter, fan filter only:         5.0e10 particles/m³, fails
high emitter, source + output capture: 5.0e9 particles/m³, passes pending bench test
```

The important finding is not the exact review threshold. The important finding is the topology: a fan filter alone is insufficient in the high-emitter case because the paper-output area is itself a modeled source path.

## Hardware implication

Rev G requires a negative-pressure fuser/exit enclosure, a serviceable filter path, and a real particle/ozone bench test before a warm printer is operated in a living space. The output tray must be treated as an emissions path, not just a place paper lands.

## Research anchors

- Fraunhofer's laser-printer/copy-machine IAQ note states that laser printers can be sources of chemical compounds plus fine and ultrafine particles, and that formal emission testing uses chambers with chemical/particle criteria. Rev G is not a certification; it is the design gate that forces a capture path before chamber testing.
