# Block schematic

```text
                      +------------------------------+
                      |          AC INLET            |
                      | fuse, switch, earth bonding  |
                      +---------------+--------------+
                                      |
               +----------------------+-----------------------+
               |                                              |
       +-------v--------+                            +--------v--------+
       | 24 V DC PSU    |                            | Fuser heater    |
       | certified/encl |                            | power module    |
       +---+---------+--+                            +---+-------------+
           |         |                                   |
           |         |                                   v
           |         |                         +---------+---------+
           |         |                         | FUSER MODULE      |
           |         |                         | heater/NTC/fuse   |
           |         |                         +-------------------+
           |         |
+----------v--+   +--v----------------+       +-------------------+
| Buck 5/3.3V |   | HV BIAS MODULE    |------>| process cartridge |
+------+-----+   | charge/dev/xfer    |       | drum/developer    |
       |         +----------+---------+       +-------------------+
       |                    ^
       v                    |
+------+--------------------+------------------------------------------+
|                     ENGINE CONTROL BOARD                             |
| MCU, motor drivers, sensors, LED bar interface, safety inputs         |
+------+---------------+---------------+----------------+--------------+
       |               |               |                |
       v               v               v                v
  paper motors    paper sensors     LED printbar     front panel
```

Hardware safety gates sit between MCU requests and hazardous outputs. The MCU can request heat/HV/exposure, but it cannot bypass cover-open or thermal cutoff.
