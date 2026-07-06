# 39. Rev E: the OFP1 wire protocol

Every revision since v1 promises a "deterministic OFP1 page-raster protocol." Rev E defines it. Reference implementation: `openframe_printer/ofp1.py` (encoder, engine-side decoder, transport budget). Generated numbers: `out/v2_ofp1_transport_budget.json`.

## Design rules

1. The engine is dumb and honest: no scaling, no reflow, no guessing. It prints exactly the lines it verified, or faults.
2. Every frame carries CRC-16/CCITT-FALSE. A corrupt frame is dropped and NACKed; corrupt bits can never reach paper.
3. Blank lines travel as SKIP runs. A fully blank Letter page is 40 bytes on the wire instead of 4.2 MB.
4. JOB_END carries a whole-page CRC so truncation and reordering fail loudly even when every frame looked fine individually.

## Frame layout (little-endian)

| offset | size | field |
|---|---:|---|
| 0 | 1 | SOF = 0xA5 |
| 1 | 1 | type |
| 2 | 2 | sequence number (wraps) |
| 4 | 2 | payload length |
| 6 | n | payload |
| 6+n | 2 | CRC-16/CCITT-FALSE over type..payload |

| Type | Name | Payload |
|---|---|---|
| 0x01 | JOB_START | version(1)=1, dpi(2), width_px(2), total_lines(2), flags(1) |
| 0x02 | LINE | line_index(2), packed row (640 B at 5120 px) |
| 0x03 | SKIP | start_line(2), count(2) — all-white lines |
| 0x04 | JOB_END | lines_covered(2), page_crc16(2) |
| 0x10 | ACK | seq_acked(2), credit(1) — engine to host |
| 0x11 | NACK | seq_refused(2), error(1) — engine to host |

Error codes: 0x01 CRC, 0x02 line order, 0x03 beyond declared lines, 0x04 coverage gap at JOB_END, 0x05 page CRC mismatch.

Lines must arrive strictly in order (LINE or SKIP). The engine is a streaming consumer feeding a line ring buffer; out-of-order delivery is a host bug and faults the job rather than being papered over.

## Transport budget (the honest part)

A worst-case page (every line carries toner) at the 12 ppm line rate:

| Quantity | Value |
|---|---:|
| LINE frame size | 650 bytes (1.5% overhead) |
| Required throughput, worst case | 7.62 Mbit/s |
| USB Full Speed bulk ceiling (19×64 B/ms) | 9.73 Mbit/s |
| FS utilization | 78% |

Verdict: USB FS can feed a worst-case page only at 78% of its theoretical bulk ceiling with zero competing traffic — workable on a bench, irresponsible as the production spec. Production transport is USB High Speed (or engine-side page RAM); FS remains the degraded 8 ppm service mode.

Engine-side buffering: a 32-line ring (20 KB, trivially inside an RP2040's 264 KB) rides through a 10 ms host hiccup (14.6 lines consumed) with margin.

## Enforced in code

`scripts/model_tests.py` proves: bit-exact round-trip under arbitrary byte chunking, blank-page SKIP compression, single-bit corruption NACKed and never printed, the CRC-16 check vector (0x29B1), and the FS-marginal verdict. `scripts/smoke_test.py` requires the generated budget artifact.
