# OpenFrame M1 Rev A schematic package

This is the board-level schematic contract for Rev A. The exact PCB layout is not frozen here; the electrical sections, nets, connectors, gating rules, and module boundaries are.

## Sheet 1: power entry and low-voltage rails

```text
J1_POWER
  AC_L ---- F1 ---- SW1 ----+---- SSR/RELAY ---- J9_FUSER heater line
                            |
                            +---- isolated AC/DC PSU ---- +24V_MOTOR
                                                        +---- +24V_AUX
                                                        +---- buck 5V ---- +5V_LOGIC
                                                                        +---- buck/LDO 3V3 ---- +3V3_LOGIC
  AC_N ---------------------+-------------------- J9_FUSER heater neutral
  PE  ------------------------------------------- frame + fuser chassis bond
```

Rules:

- Fuser heater branch and isolated PSU branch split after fuse/switch.
- Protective earth bonds to chassis and fuser metalwork.
- Logic ground and chassis bond are handled at the safety-reviewed bonding point only.
- Fuser heater cannot be powered through the MCU board copper except for isolated control of relay/SSR.

## Sheet 2: interlock gate

```text
COVER_CLOSED_LOOP
ESTOP_LOOP_CLOSED
THERMOSTAT_LOOP_CLOSED
THERMAL_FUSE_CLOSED
MCU_WATCHDOG_OK
PSU_FAULT_N
        |
        v
hardware AND / safety gate
        |
        +---- HV_ENABLE_HW
        +---- LED_OE_HW
        +---- FUSER_HEATER_ENABLE_HW
        +---- MAIN_MOTOR_ENABLE_ALLOWED
```

Rules:

- Firmware request plus hardware gate is required for hazardous outputs.
- Firmware cannot assert a hazardous output when the hardware gate is false.
- Cover open removes HV, LED OE, fuser heat, and motor enable.
- Thermostat or thermal fuse open removes fuser heat even if firmware is crashed.

## Sheet 3: MCU and timing

MCU class: RP2040 or equivalent dual-core MCU with deterministic PIO/DMA timing.

| Function | Signal group |
|---|---|
| LED timing | LVDS clock, data0, data1, latch, OE request |
| Paper timing | pre-reg, image-sync, fuser-exit, exit sensor interrupts |
| Motor control | main motor enable/encoder, pickup step/dir, registration step/dir |
| HV control | three DAC outputs, three ADC monitor inputs, HV fault input |
| Fuser control | thermistor ADC, tach input, heater request output |
| UI/service | I2C display/buttons, USB serial/service |

## Sheet 4: LED bar interface

```text
MCU PIO/DMA -> LVDS driver -> J6_LED_BAR
  LED_CLK_P/N
  LED_DATA0_P/N
  LED_DATA1_P/N
  LED_LATCH_P/N
  LED_OE_HW
  +5V_LED switched rail
  +3V3_LED_IO
  LED_TEMP_NTC
```

Timing:

- 5120 bits per line.
- 640 bytes per line.
- 682.8 µs line period at 12 ppm.
- 20 MHz shift clock recommended.
- Line strobe uses fractional accumulator timing.

## Sheet 5: HV module interface

```text
+24V_AUX -------------------- J7_HV_MODULE +24V_HV
HV_ENABLE_HW ---------------- J7_HV_MODULE HV_ENABLE
DAC0 PCR_DAC ---------------- J7_HV_MODULE PCR_SET
DAC1 DEV_DAC ---------------- J7_HV_MODULE DEV_SET
DAC2 XFER_DAC --------------- J7_HV_MODULE XFER_SET
ADC0 PCR_MON <--------------- J7_HV_MODULE PCR_MON
ADC1 DEV_MON <--------------- J7_HV_MODULE DEV_MON
ADC2 XFER_MON <-------------- J7_HV_MODULE XFER_MON
HV_FAULT_N <----------------- J7_HV_MODULE HV_FAULT_N

J7 potted module outputs:
  PCR_HV  ---- spring contact ---- primary charge roller
  DEV_HV  ---- spring contact ---- developer roller
  XFER_HV ---- spring contact ---- transfer roller
```

HV targets:

Rev D warning: the PCR target below is historical and retired. Active PCR values are in `hardware/ofp_m1_revD_hv_bias_channels.csv` and generated `out/v2_hv_bias_channels.json`.

- PCR: -720 V nominal, -500 to -900 V range, 200 µA limit.
- Developer: -320 V nominal, -150 to -500 V range, 300 µA limit.
- Transfer: +1600 V nominal, +700 to +2500 V range, 500 µA limit.

## Sheet 6: fuser module interface

```text
FUSER_HEATER_ENABLE_HW -> isolated SSR/relay driver -> J9_FUSER heater line
J9_FUSER thermistor pair -> analog front-end -> ADC
J9_FUSER thermostat loop -> interlock gate
J9_FUSER thermal fuse loop -> interlock gate
J9_FUSER tach -> MCU interrupt
J9_FUSER PE -> chassis bond
```

Rules:

- Thermistor open/short faults before heater enable.
- Thermostat and thermal fuse are independent of firmware.
- Fuser fan remains available after heater fault.

## Sheet 7: sensors and motors

Sensors are active-low where possible so a broken wire tends to look like a fault instead of a false safe signal.

| Sensor | MCU behavior |
|---|---|
| PRE_REG_SENSOR_N | lead-edge timeout from pickup start |
| IMAGE_SYNC_SENSOR_N | starts image line-zero offset |
| FUSER_EXIT_SENSOR_N | confirms sheet left fuser nip |
| EXIT_SENSOR_N | confirms sheet left printer |
| TRAY_PRESENT_N | blocks pickup if tray absent |
| PAPER_PRESENT_N | blocks pickup if no paper |

Motor outputs are low-voltage only. The paper-motion rig can be built and tested without any hot/HV/optical module installed.
