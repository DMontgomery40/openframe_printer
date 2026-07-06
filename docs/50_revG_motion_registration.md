# 50. Rev G motion registration and line-pitch budget

Previous revisions computed the nominal process speed, drum rpm, and station delays. They did not prove that the engine places lines correctly when roller diameter, slip, motor speed, and load change.

Generated gate: `out/v2_motion_registration_budget.json`  
Executable model: `openframe_printer/motion_registration.py`

## Finding

A 600 dpi line is **42.333 µm** tall. Open-loop process-speed error becomes page-scale error immediately:

| Open-loop speed error | Letter stretch error | Line error |
|---:|---:|---:|
| 0.1% | 0.279 mm | 6.6 lines |
| 0.5% | 1.397 mm | 33.0 lines |
| 1.0% | 2.794 mm | 66.0 lines |

That is too large to hide in a firmware constant.

## Rev G contract

LED line firing must be slaved to measured drum position, not only to commanded motor timing. The registration sensor sets the page phase/lead-edge offset; it does not prove continuous line spacing after the page starts moving.

Recommended first build:

```text
4096 CPR encoder on drum axis
quadrature decode = 16,384 physical edges/rev
edge pitch = 5.75 µm = 0.136 lines
passes quarter-line quantization gate
```

A 2048 CPR encoder without interpolation gives **11.50 µm / 0.272 line** edge pitch, just outside the conservative quarter-line gate. It can pass only with timer interpolation or a higher CPR encoder.

## Registration timestamp gate

At 62 mm/s:

| Timestamp jitter | Position error | Gate |
|---:|---:|---|
| 50 µs | 3.1 µm | pass |
| 150 µs | 9.3 µm | pass |
| 300 µs | 18.6 µm | fail |

So the firmware interface needs timestamped sensor edges, not slow polling.
