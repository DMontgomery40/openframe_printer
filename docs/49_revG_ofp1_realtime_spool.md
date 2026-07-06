# 49. Rev G OFP1 real-time spool budget

Rev E made OFP1 a real wire protocol. That was necessary, but not sufficient: a CRC-clean stream can still underrun a moving electrophotographic engine if the host pauses after the page clutch starts.

Generated gate: `out/v2_ofp1_realtime_spool.json`  
Executable model: `openframe_printer/ofp1_realtime.py`

## Finding

The Rev E transport artifact used a 10 ms hiccup target and a 32-line decoded ring buffer. At 600 dpi, 12 ppm, and 5120 pixels/line, decoded raster drain is about **937 kB/s**. The 32-line ring is only **20,480 bytes**, which covers about **21.85 ms** of no-host time.

Rev G makes the first-build host-pause target **100 ms**, not because USB guarantees that value, but because a moving page needs engineering slack. That target requires **93,733 bytes** of decoded line buffer.

## Consequences

| Case | Result |
|---|---|
| Rev E 32-line ring, 12 ppm, 100 ms pause | underruns |
| RP2040-class 128 KiB ring, USB FS at 80% ceiling | passes 100 ms pause if prefilled |
| USB FS at 75% ceiling, 12 ppm worst-case page | cannot sustain drain rate |
| USB FS at 8 ppm with 128 KiB ring | passes 100 ms pause |
| USB HS with 128 KiB ring | passes 12 ppm gate |

The production contract is now explicit:

1. **USB High Speed or external page spool RAM** is required for 12 ppm production.
2. USB Full Speed may remain as service/debug mode only if the engine slows and/or pre-spools before clutch start.
3. The firmware cannot start paper motion merely because the first OFP1 frame decoded correctly; it must prove spool margin.

## New build gate

A job may start the registration clutch only when:

```text
decoded_buffer_prefill_bytes >= bytes_needed_for_declared_pause_target
and sustained_host_rate >= decoded_line_drain_rate for selected ppm
```

For the Rev G first build:

```text
pause target: 100 ms
12 ppm buffer need: 93,733 bytes
recommended first ring: 128 KiB decoded line ring
production transport: USB High Speed or external page spool RAM
```

## Research anchors

- Raspberry Pi Pico product page: RP2040 has 264 kB on-chip SRAM and a USB 1.1 controller/PHY.
- Microsoft USB bulk-transfer documentation: bulk transfer has CRC/retry integrity, but bandwidth is not reserved; full-speed bulk max packet size is 64 bytes and high-speed bulk max packet size is 512 bytes.
