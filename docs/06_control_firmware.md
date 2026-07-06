# Control firmware

The engine controller is a deterministic motion/safety controller. It does not parse PDFs. It receives a rasterized page and a job plan from the host board.

## Responsibilities

- maintain hard state machine
- enforce interlocks
- heat fuser to target range
- feed sheet
- register sheet timing
- stream LED exposure lines
- control motor speed
- monitor sensors for jams
- shut down hazardous outputs on faults
- return readable fault codes

## Non-responsibilities

- cloud setup
- account login
- PDF rendering
- network discovery
- mobile app behavior
- telemetry

## State machine

```text
SAFE_IDLE
  - all hazardous outputs disabled
  - motors off
  - accepts job if cover closed and no faults

WARMING_FUSER
  - heater controlled to target
  - HV disabled
  - LED disabled

READY
  - fuser at temp
  - motors off
  - page can start

FEEDING
  - pickup motor active
  - expects pickup sensor transition within timeout

REGISTERING
  - registration roller controls exact paper timing
  - image clock origin is established

IMAGING
  - process motor locked to line rate
  - LED line data streamed
  - HV biases enabled only in this window

FUSING
  - fuser motor active
  - heater maintains target

EXITING
  - exit sensor must clear within timeout

COMPLETE
  - page count increments
  - outputs return to safe idle or next-page ready
```

## Fault logic examples

| Fault | Trigger | Immediate action |
|---|---|---|
| DOOR_OPEN | cover loop opens | disable HV, LED, fuser heater; stop imaging |
| FUSER_OVERTEMP | thermistor above limit | disable heater; fault latch |
| FUSER_UNDERTEMP | below print minimum during fusing | stop accepting pages; finish/abort safely |
| PAPER_LATE_REG | pickup sensor ok but registration not reached | stop feed; jam fault |
| PAPER_STUCK_EXIT | exit sensor blocked too long | stop motors; jam fault |
| HV_FAULT | HV module reports overcurrent/undervoltage | disable HV; fault latch |
| MOTOR_STALL | driver stall or encoder mismatch | stop motors; fault latch |

## Protocol

Host sends:

```text
OFP1_JOB_BEGIN
page_width_px
page_height_lines
resolution_dpi
process_speed_mm_s
line_count
checksum

OFP1_LINE_DATA repeated line_count times

OFP1_JOB_END
```

Engine replies:

```text
READY
WARMING
PRINTING line=N
COMPLETE page_id=N
FAULT code=...
```

The protocol is intentionally boring. Debuggability beats cleverness.
