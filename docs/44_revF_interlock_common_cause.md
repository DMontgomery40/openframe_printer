# 44. Rev F: interlock common-cause correction

Engine: `openframe_printer/interlock_faults.py`. Artifact: `out/v2_interlock_fault_analysis.json`.

## Finding

Rev E's interlock model was useful but too narrow. It proved the dual-chain topology survives independent electrical stuck-at faults. It did **not** model a single mechanical common-cause failure: one cracked, taped, misaligned, or defeated door actuator causing both switch contacts for the same door to read closed.

That matters because two contacts moved by the same plastic tab are not truly diverse safeguards.

## Rev F model result

| Topology | Fault universe | Single-fault safe? |
|---|---|---:|
| A: one switch loop | electrical stuck-at | no |
| B: Rev E dual electrical chains | independent electrical stuck-at only | yes |
| B: Rev E dual electrical chains | adds shared door-actuator common cause | no |
| C: Rev F diverse topology | electrical + shared actuator common cause | yes |

Topology B fails when `door_main_cover_common_actuator:stuck_closed_both_chains` is injected and the main cover is open: both chains think the door is closed, so adversarial firmware can energize hazards.

## Rev F topology C

Rev F adds a third, physically diverse energy-removal path:

```text
Door contact A  -> logic enable gates
Door contact B  -> independent energy-path relay/SSR
Door energy separator -> physical contact/shroud/contactor opened by the access door
```

The third path must not be operated by the same switch tab as contacts A and B. Acceptable examples for the first rig:

- shrouded HV cartridge contacts that physically separate when the process door opens,
- fuser heater contactor opened by a positive-opening access mechanism,
- LED VLED rail contact block physically separated from the logic-sense switch actuator.

Firmware may diagnose faults, but safety must not depend on firmware behaving.

## Research/safety grounding

IEC 62368-style hazard-based safety uses single-fault reasoning around safeguards; public summaries and copies describe single-fault conditions as a basic part of the safety model:

- `https://www.belfuse.com/resource-library/tech-paper/iec-62368-1-an-introduction-to-the-new-safety-standard-for-ict-and-av-equipment`
- `https://ib-lenhardt.com/product-testing/safety-standard-iec-62368-1`
- `https://www.china-gauges.com/common/down/name/5710ecb863a33.pdf`

## Enforced in code

New model tests prove:

- Rev E topology B fails the shared actuator fault.
- Rev F topology C survives the same single fault.
- Defeating topology C requires at least two faults, such as shared actuator defeat plus the matching physical energy separator stuck closed.
