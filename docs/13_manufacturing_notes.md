# Manufacturing notes

## Design-for-repair rules

- no hidden clips where screws are appropriate
- no melting plastic stakes for serviceable parts
- rollers accessible from one service side
- fuser removal with captive screws
- keyed connectors with labels printed on board and harness
- paper path visible when service panel opens
- QR code on each module links to public service page
- consumable modules expose mechanical fit, not authentication hostage logic

## Suggested first physical articles

| Article | Purpose |
|---|---|
| A0 paper motion rig | validate paper path only |
| A1 cold timing rig | validate registration and line timing |
| A2 fuser thermal rig | validate heater control separately |
| A3 process bench | characterize drum/developer/transfer/fuser stack |
| A4 integrated alpha | first complete enclosed print |

## Materials/process guesses

| Part | Early build material/process |
|---|---|
| Main frame | bent sheet metal or CNC/router-cut aluminum plates |
| Paper guides | injection molded later, 3D printed/SLS prototype now |
| Roller shafts | stainless/steel rod with bearings/bushings |
| Service panels | injection molded later, printed/CNC prototype now |
| Gear train | off-the-shelf gears first, custom molded later |
| Harnessing | labeled JST/Molex-style keyed connectors |

## Open documentation package

Each production unit should ship with a public package:

- exploded view
- BOM with purchasable service parts
- fault code table
- roller replacement guide
- process module replacement guide
- fuser replacement guide
- firmware recovery guide
- electrical block diagram
- IPP/local networking guide
