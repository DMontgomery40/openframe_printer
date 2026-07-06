# 40. Rev E/F: interlock fault analysis

The safety docs promise "firmware cannot override cover-open state." That is necessary and insufficient: the question a certification reviewer and the physics will ask is *which single fault leaves a hazard live with a door open?* Appliance-safety thinking expects safeguards to survive single-fault conditions.

Engine: `openframe_printer/interlock_faults.py`. Artifact: `out/v2_interlock_fault_analysis.json`. Firmware is modeled adversarially — every hazard request line driven high — because firmware is exactly the thing the hardware chain must not trust.

## Result for the chain as documented: topology A

One NC switch per access door, one series loop, one AND gate per hazard. Exhaustive single-stuck-at enumeration finds these single-point-failure nets:

| Fault | Effect with a door open |
|---|---|
| Any cover switch welded/stuck closed | loop stays closed; all hazards can be live |
| Loop wire shorted to enable rail | same |
| HV / LED / fuser enable gate output stuck high | that hazard live |

These are not exotic faults. Welded contacts, cracked actuators, and chafed harnesses are standard aging failures of exactly these parts.

## Rev E proposal: topology B

Each door opens two contacts feeding two independent electrical cut paths:

- Chain A feeds the logic enable gates.
- Chain B independently cuts the energy path via a series relay/SSR feeding the HV module, LED VLED rail, and fuser drive.

A hazard is live only if its request, its logic gate, and the power path all agree. Under the Rev E fault universe — independent electrical stuck-at faults — topology B has zero single-fault violations.

## Rev F correction: topology B still fails mechanical common cause

Rev E did not model one realistic single fault: a shared door actuator/common latch failure that makes both contacts for the same door read closed. Two switches moved by the same plastic tab are not diverse safeguards.

Rev F injects faults like:

```text
door_main_cover_common_actuator:stuck_closed_both_chains
```

With the main cover open, topology B can still energize hazards because both electrical chains believe the door is closed.

## Rev F requirement: topology C

Topology C keeps topology B and adds a third, physically diverse energy-removal path:

```text
Door contact A          -> logic enable gates
Door contact B          -> independent energy relay/SSR
Door energy separator   -> physical contact/shroud/contactor opened by the access door
```

The third path must not be moved by the same actuator as contacts A/B. It represents a shrouded cartridge HV contact, positive-opening fuser contactor, or physically separated LED VLED contact block.

## Enforced in code

`scripts/model_tests.py` proves:

- topology A is not single-fault safe,
- topology B survives independent electrical stuck-at faults,
- topology B fails the shared door-actuator common-cause fault,
- topology C survives that single fault,
- defeating topology C requires at least two faults.

`NEXT.md` rig 3e now tests topology C, not the narrower Rev E dual-chain result.
