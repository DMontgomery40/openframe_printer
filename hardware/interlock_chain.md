# Interlock chain

Rev F active design: topology C. The old Rev A single-loop interlock is retained only as historical context because the fault model found seven single-point failures. Rev E's dual electrical chain fixed independent stuck-at electrical faults, but a single shared door actuator can still make both contacts read closed. Rev F adds a physically diverse energy separator.

## Topology C minimum

Each hazardous-access door needs three independent effects:

```text
Door opens
  ├─ Chain A contact opens: MCU logic/sense path
  ├─ Chain B contact opens: hardware enable-gate path
  └─ Energy separator opens: mechanically linked relay/contactor/thermal-power separator in the hazardous energy path
```

Do not implement Chain A and Chain B with one shared plastic flag that presses two microswitches unless the separate energy separator also opens when the cover moves. The generated model treats `door_<name>_common_actuator:stuck_closed_both_chains` as one plausible single fault and proves Rev E topology B fails it.

## Signals

```text
INTERLOCK_CHAIN_A_OK = COVER_A_OK AND SERVICE_PANEL_A_OK AND REAR_DOOR_A_OK
INTERLOCK_CHAIN_B_OK = COVER_B_OK AND SERVICE_PANEL_B_OK AND REAR_DOOR_B_OK
ENERGY_PATH_OK       = COVER_ENERGY_OK AND SERVICE_PANEL_ENERGY_OK AND REAR_DOOR_ENERGY_OK

HV_ENABLE_ACTUAL     = HV_ENABLE_REQ     AND INTERLOCK_CHAIN_B_OK AND ENERGY_PATH_OK AND HV_MODULE_OK
LED_OE_ACTUAL        = LED_OE_REQ        AND INTERLOCK_CHAIN_B_OK AND ENERGY_PATH_OK
FUSER_ENABLE_ACTUAL  = FUSER_REQ         AND INTERLOCK_CHAIN_B_OK AND ENERGY_PATH_OK AND THERMAL_FUSE_OK AND OVERTEMP_GATE_OK
```

The MCU reads Chain A, Chain B, and the energy-path auxiliary sense so it can explain the fault, but the MCU is not allowed to be the only thing that removes hazardous energy.

## Required generated gate

Run:

```bash
python3 -m openframe_printer.design_report && python3 scripts/smoke_test.py && python3 scripts/model_tests.py
```

The active artifact is:

```text
out/v2_interlock_fault_analysis.json
```

Required values:

```text
topology_b_rev_e_electrical_fault_model.safe_under_all_single_faults = true
topology_b_rev_e_with_mechanical_common_cause.safe_under_all_single_faults = false
topology_c_rev_f_diverse_energy_path.safe_under_all_single_faults = true
```

## Fault behavior

If any interlock path opens or disagrees:

- fuser heater disabled
- HV disabled
- LED output disabled
- motors stop or coast according to the jam-safe motion strategy
- job aborted
- fault latched until covers close and the user acknowledges

## Bench fault-injection cases

At minimum, physically inject:

- one welded contact on Chain A
- one welded contact on Chain B
- one shorted enable-gate net
- one forced-high firmware request line
- one shared door actuator taped/wedged closed while the door is physically open
- one energy separator contact welded closed

Topology C is expected to survive every single item above. Some double faults remain dangerous; the point of Rev F is to make those double faults observable before the second fault arrives.
