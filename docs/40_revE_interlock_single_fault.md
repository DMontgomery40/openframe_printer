# 40. Rev E: interlock single-fault analysis

The safety docs promise "firmware cannot override cover-open state." That is necessary and insufficient: the question a certification reviewer (and physics) will ask is *which single component failure leaves a hazard live with a door open?* Appliance-safety thinking (IEC 62368-class) expects safeguards to survive any one fault.

Engine: `openframe_printer/interlock_faults.py`. Artifact: `out/v2_interlock_fault_analysis.json`. Firmware is modeled adversarially — every hazard request line driven high — because firmware is exactly the thing the hardware chain must not trust.

## Result for the chain as documented (topology A)

One NC switch per access door, one series loop, one AND gate per hazard. Exhaustive single-stuck-at enumeration finds **7 single-point-failure nets**:

| Fault | Effect with a door open |
|---|---|
| Any cover switch welded/stuck closed (3 nets) | loop stays closed; all hazards can be live |
| Loop wire shorted to enable rail | same |
| HV / LED / fuser enable gate output stuck high (3 nets) | that hazard live |

These are not exotic faults. Welded contacts and chafed harnesses are the standard aging failures of exactly these parts.

## Rev E proposal (topology B)

Each door opens **two independent contacts** feeding **two independent cut paths**:

- Chain A feeds the logic enable gates (as today).
- Chain B independently cuts the energy path via a series relay/SSR feeding the HV module, LED VLED rail, and fuser drive.

A hazard is live only if its request AND its logic gate AND the power path all agree. Exhaustive enumeration: **zero single-fault violations**; every defeat requires two simultaneous faults (45 such pairs enumerated, e.g. both contacts of one door welded, or a stuck gate plus a welded relay).

## Requirement going forward

Adopt topology B before the first HV or fuser rig is energized. Hardware cost is one extra contact block per door and one relay/SSR. `scripts/smoke_test.py` asserts topology A is not single-fault safe and topology B is, so the analysis cannot silently rot as the chain evolves.
