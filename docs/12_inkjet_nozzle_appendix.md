# Inkjet nozzle appendix

M1 does not start with inkjet. This appendix exists because the long-term philosophical enemy is consumer inkjet abuse, and because a future OpenFrame Ink product would need to own the nozzle/fluid problem instead of hand-waving it away.

## Why inkjet is not M1

Inkjet requires controlling:

- nozzle diameter and surface finish
- droplet volume
- firing waveform
- ink viscosity and surface tension
- pressure regulation
- meniscus stability
- clogging/drying behavior
- cleaning cycles
- cap/wiper station
- waste ink path
- color management
- thermal or piezo actuator reliability

That is a materials science and microfabrication project, not just a firmware project.

## Future inkjet target envelope

These are research targets to turn into lab experiments, not final specs.

| Parameter | Early target range |
|---|---:|
| Nozzle diameter | 10-30 um |
| Droplet volume | 5-20 pL |
| Native nozzle pitch | 300-1200 dpi equivalent |
| Firing frequency | 5-20 kHz |
| Ink viscosity | low single-digit to low double-digit cP, formulation-specific |
| Meniscus pressure | slightly negative relative to ambient |
| Maintenance | cap, wipe, purge, waste reservoir |
| Printhead module | user-replaceable, no printer lockout |

## Architecture options

### Thermal inkjet

- lower external actuator complexity
- uses heater resistor pulse to vaporize bubble
- tightly coupled to ink chemistry
- printhead is consumable-like

### Piezo inkjet

- more expensive actuator stack
- works with wider fluid range
- waveform tuning is harder
- potentially longer printhead life

## OpenFrame Ink strategy

The sane path is not to make the first printer inkjet. The sane path is:

1. Build OpenFrame M1 as monochrome electrophotographic.
2. Establish local-first firmware, service model, module standards, and trust.
3. Build a printhead lab rig, not a printer, for inkjet experiments.
4. Characterize one black ink, one printhead module, one cleaning station.
5. Only then productize inkjet.

## Minimum inkjet lab rig

```text
ink reservoir -> pressure regulator -> printhead module -> cap/wiper station
       |               |                    |
   level sensor     pressure sensor      nozzle plate microscope inspection

motion stage under printhead
  -> paper/film sample
  -> camera inspection
  -> droplet/line quality metrics
```

The first useful inkjet milestone is not a full printer. It is a repeatable black line without clogs after 24 hours idle.
