# Electronics schematic plan

This file is the board-level schematic map for M1. It is intentionally written as a net-level contract before committing to a PCB layout.

## Boards

```text
AC inlet + fuse + switch
  -> certified enclosed AC/DC PSU: 24 V main rail
  -> fuser heater power module: isolated/guarded heater drive
  -> control board buck rails: 5 V, 3.3 V
  -> HV bias module: interlock-gated, current-limited charge/develop/transfer rails
```

## Control board sections

```text
+-------------------------------------------------------------+
| RP2040 / equivalent MCU                                     |
|                                                             |
| USB device  UART debug  SWD                                 |
|                                                             |
| Motor drivers: pickup, registration/process, fuser/exit     |
| Sensor inputs: tray, reg, transfer, fuser, exit, covers      |
| LED head: data, clock, latch, line_sync, output_enable       |
| HV controls: enable, charge_pwm, dev_pwm, transfer_pwm       |
| Fuser: thermistor_adc, heater_pwm, zero_cross/ssr_enable     |
| Safety: hardware interlock loop sense, e-stop/fuse sense     |
+-------------------------------------------------------------+
```

## Main nets

| Net | Voltage/domain | Notes |
|---|---|---|
| VIN_24V | 24 V DC | motors, fans, low-voltage fuser control |
| VIN_5V | 5 V DC | sensors, LED logic if needed |
| VDD_3V3 | 3.3 V DC | MCU and logic |
| HV_EN_SAFE | logic | AND of MCU request and hardware interlock loop |
| FUSER_EN_SAFE | logic | AND of MCU request, thermal fuse continuity, cover closed |
| LED_OE_SAFE | logic | disabled when cover open or page not in image state |
| MOTOR_EN | logic | global motor driver enable |
| NTC_FUSER_ADC | analog | fuser thermistor divider |
| COVER_LOOP_OK | logic | independent cover interlock sense |
| PAPER_REG_SENSE | logic | registration sensor |
| PAPER_EXIT_SENSE | logic | exit sensor |

## Power budget rough targets

| Load | Target |
|---|---:|
| Host board | 5-10 W |
| MCU/control board | 1-3 W |
| Motors/fans | 20-60 W active |
| HV bias module | <5 W average |
| LED exposure | 2-15 W active depending head |
| Fuser | 300-700 W while heating, lower duty while printing |

## Hard safety design rule

The MCU is not the only safety device. Cover-open and over-temperature must remove hazardous energy through hardware gating, not just firmware state.

Minimum hardware gates:

```text
cover interlock loop ----+----> HV module enable gate
                         +----> LED output enable gate
                         +----> fuser heater gate

thermal fuse ------------+----> fuser heater power series cutoff

fuser thermistor --------+----> MCU ADC
                         +----> analog over-temp comparator, optional v1
```

## Pseudo-schematic files

- `hardware/control_board_pinmap.csv` maps MCU pins to functions.
- `hardware/pseudo_netlist.net` expresses the intended connectivity in text.
- `hardware/interlock_chain.md` documents the non-firmware safety chain.
