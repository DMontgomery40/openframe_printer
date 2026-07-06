# 18. LED exposure bar spec

OpenFrame M1 Rev A uses a fixed LED printbar instead of a spinning laser scanner. This removes polygon motor alignment, mirror dust problems, scan-line bow, and laser-class service complexity.

## Optical constants

| Parameter | Rev A target |
|---|---:|
| Active pixels | 5120 |
| Native resolution | 600 dpi |
| Pixel pitch | 42.333 µm |
| Active width | 216.747 mm |
| Starting wavelength | 780 nm |
| Nominal exposure target | 0.45 µJ/cm² |
| Exposure sweep | 0.15-1.00 µJ/cm² |

## Timing constants at 12 ppm

| Parameter | Value |
|---|---:|
| Process speed | 62.0 mm/s |
| Line rate | 1464.567 lines/s |
| Line period | 682.796 µs |
| 1-bit line payload | 640 bytes |
| Raw raster rate | 7.498 Mbit/s |
| Recommended shift clock | 20 MHz with two data lanes, or >30 MHz with one data lane |

At 20 MHz on one data lane, a 5120-bit line shifts in 256 µs, which is 37.5% of the 682.796 µs line period. That does **not** satisfy the Rev B 25% line-time budget. At 20 MHz split across two 2560-bit data lanes, the shift time is 128 µs, or 18.75% of the line period. Therefore Rev B either uses two data lanes or raises the single-lane shift clock above 30 MHz.

## Electrical interface

| Signal | Type | Notes |
|---|---|---|
| LED_CLK_P/N | LVDS | 20 MHz recommended clock |
| LED_DATA0_P/N | LVDS | First data lane |
| LED_DATA1_P/N | LVDS | Second data lane for margin or split bar |
| LED_LATCH_P/N | LVDS | Latches shifted line data |
| LED_OE_HW | 3.3 V hardware-gated | Output enable cannot be asserted with cover open |
| LED_TEMP_NTC | analog | Thermal monitor for LED bar |
| +5V_LED | switched 5 V | Removed by `LED_SAFE_EN` gate |
| +3V3_LED_IO | 3.3 V | Logic only |

## Firmware buffering

Rev A firmware uses two 640-byte line buffers:

1. Buffer A shifts into the LED bar.
2. Buffer B is filled from the raster stream.
3. On line latch, the buffers swap.
4. A fractional line-period accumulator prevents cumulative drift.

The line timer must not round 682.796 µs to a fixed integer delay and repeat it for a whole page. That creates visible vertical scaling drift. The firmware skeleton uses a phase accumulator requirement for this reason.

## Calibration print sequence

1. HV disabled, LED disabled: verify timing only.
2. LED enabled into photodiode jig: verify line payload and OE shape.
3. LED exposure onto sacrificial OPC strip: sweep exposure without toner.
4. Add developer and transfer: sweep charge/developer/transfer values.
5. Lock density table only after multiple toner and humidity runs.
