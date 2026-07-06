# Architecture

OpenFrame M1 has four layers:

```text
User device
  -> IPP/AirPrint/Mopria-facing local print service
    -> rasterizer / scheduler
      -> OFP1 page-stream protocol
        -> engine controller
          -> motors, sensors, LED exposure, HV biases, fuser control
```

## Major physical subsystems

```text
+-------------------------------------------------------------+
|                         OpenFrame M1                         |
|                                                             |
|  +------------------+     +------------------------------+  |
|  | Host/network SBC |<--->| RP2040-class engine control   |  |
|  | IPP + rasterizer | USB | deterministic real-time I/O   |  |
|  +------------------+     +---------------+--------------+  |
|                                          |                 |
|       +-------------+--------------------+-------------+   |
|       |             |                    |             |   |
|   Motors        Sensors             LED bar         Power/HV |
|       |             |                    |             |   |
|  paper path    jam/door/temp       exposure       fuser/HV   |
|                                                             |
+-------------------------------------------------------------+
```

## Process subsystem

Monochrome electrophotography:

1. Condition/clean drum.
2. Charge photoconductor surface with a primary charge roller.
3. Expose charged drum surface with LED bar line image.
4. Develop latent image with toner on developer roller.
5. Transfer toner image to paper at transfer nip.
6. Fuse toner to paper with heated pressure rollers.
7. Discharge/clean drum for next rotation.

## Why LED exposure

A normal laser printer uses a laser diode, polygon mirror, scan optics, beam detect, and precise optics alignment. That is buildable but annoying. LED exposure uses a fixed-width linear printhead that writes one line at a time as the drum rotates. It removes the spinning polygon mirror and makes the first open hardware printer mechanically more plausible.

## Board split

| Board | Purpose |
|---|---|
| Host board | networking, IPP, PDF/text/image ingest, rasterization, web UI |
| Engine controller | real-time timing, motors, sensors, LED line strobe, interlocks |
| HV module | charge/develop/transfer biases, current-limited, interlock-gated |
| Fuser power module | heater drive, thermistor readout, thermal fuse chain, interlock-gated |
| Front panel board | buttons, display, status LEDs |

## Firmware state machine

```text
OFF
  -> SAFE_IDLE
  -> WARMING_FUSER
  -> READY
  -> FEEDING
  -> REGISTERING
  -> IMAGING
  -> FUSING
  -> EXITING
  -> COMPLETE
  -> SAFE_IDLE

Fault states:
  DOOR_OPEN
  PAPER_JAM
  OVER_TEMP
  UNDER_TEMP
  HV_FAULT
  MOTOR_STALL
  SENSOR_IMPLAUSIBLE
  LED_FAULT
```
