# 21. Paper path geometry Rev A

The paper path is deliberately simple: one tray, one pickup/separation stage, one registration nip, one transfer nip, one fuser, one output path. No duplexer, scanner, color carousel, envelope path, or photo media path in Rev A.

## Station positions

All Y positions are measured from the tray leading-edge home position.

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

## Motion constants

| Parameter | Value |
|---|---:|
| Process speed | 62.0 mm/s |
| Registration hold | 120 ms |
| Jam window | ±20% of expected transit time |
| Pickup roller diameter | 18 mm |
| Registration roller diameter | 12 mm |
| Fuser roller diameter | 24 mm |
| Exit roller diameter | 16 mm |

## Sensor philosophy

Each sensor is cheap and individually replaceable. The printer should show exact service messages instead of vague paper-jam nonsense.

Examples:

- `PRE_REG_SENSOR late`: pickup/separation problem.
- `IMAGE_SYNC_SENSOR late`: registration release problem.
- `FUSER_EXIT_SENSOR late`: fuser nip or transport drag problem.
- `EXIT_SENSOR stuck active`: paper remained in output path.

## Cold rig pass/fail

The first build does not need toner, HV, fuser heat, or LED output. It needs to move paper repeatably.

A passing cold rig feeds 100 Letter sheets at 62.0 mm/s with:

- no double-feeds,
- no missed pickup,
- no late pre-registration event,
- registration release within the line-sync budget,
- no sheet skew severe enough to scrape the process cartridge envelope,
- all sensor events inside the generated windows in `out/v2_motion_events.json`.
