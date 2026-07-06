# Raster and timing

## Page raster

M1 consumes 1-bit monochrome raster lines. All higher-level input is handled by the host stack.

| Layer | Input | Output |
|---|---|---|
| User app | PDF, text, image, web page | OS print job |
| Local print service | IPP job | normalized page description |
| Rasterizer | page description | 1-bit PBM-style raster |
| Scheduler | raster + engine config | OFP1 line stream |
| Engine controller | OFP1 line stream | timed LED exposure |

## 600 dpi letter sizing

| Parameter | Value |
|---|---:|
| Letter width | 8.5 in |
| Letter height | 11 in |
| Width at 600 dpi | 5100 px |
| Height at 600 dpi | 6600 lines |
| Raw page bits | 33.66 Mbit |
| Raw page bytes | 4.21 MB |

At 12 ppm, line timing is the important constraint:

```text
12 ppm = 5 seconds/page
with 30.6 mm inter-page gap, process speed = 62.0 mm/s
600 dpi line pitch = 0.04233 mm
line rate = 1465 lines/s
line period = 682.5 us
```

That is not a scary data rate. It is a real-time coordination problem.

## Timing origin

The registration sensor creates the page timing origin. The engine does not assume the paper is exactly where the host thinks it is.

```text
registration_sensor_edge
  -> wait calibrated offset to transfer nip
  -> start image line 0
  -> step/encoder process motion
  -> strobe LED line N every line_period
```

## Data buffering

Minimum buffers:

| Buffer | Size target |
|---|---:|
| Host raster page | full page, 4-8 MB mono |
| Engine line buffer A | one active line |
| Engine line buffer B | next line |
| Engine job metadata | <4 KB |

The first prototype can stream from host to engine over USB with double buffering. Later versions can add engine-side RAM for full-page buffering.
