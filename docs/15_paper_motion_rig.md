# 15. Paper motion rig

The paper-motion rig is the first physical OpenFrame M1 build. It is cold: no HV, no fuser heat, no LED optical output, no toner.

## Installed in Rig 1

- frame,
- tray,
- pickup roller,
- separation pad,
- registration roller,
- dummy fuser rollers,
- exit roller,
- sensors,
- low-voltage PSU,
- controller board,
- motors.

## Station map

| Station | Y position |
|---|---:|
| Tray leading-edge home | 0 mm |
| Pickup nip | 25 mm |
| Separation nip | 32 mm |
| Pre-registration sensor | 88 mm |
| Registration nip | 112 mm |
| Image sync sensor | 138 mm |
| Transfer nip | 180 mm |
| Fuser entry | 255 mm |
| Fuser exit | 285 mm |
| Exit sensor | 340 mm |
| Output roller | 360 mm |

## Timing target

At 62.0 mm/s, the rig checks sensor arrivals against the generated data in `out/v2_motion_events.json`. The default jam window is ±20%.

## Pass/fail

- 100 sheets feed without double-feed.
- Registration hold/release works repeatably.
- Sensor timing stays inside generated windows.
- Opening the cover loop forces all hazardous-request outputs low.
- The line strobe can run for 6600 Letter-page lines without cumulative drift.
