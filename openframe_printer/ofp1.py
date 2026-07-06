from __future__ import annotations

"""OFP1: the OpenFrame page-raster wire protocol, defined and implemented.

Every revision so far *names* OFP1 (README, job plans, architecture doc) and
none defines it. Rev E makes it real: a deterministic binary framing for
host -> engine 1-bpp raster delivery, a reference encoder, and a reference
engine-side decoder that reconstructs the page bit-exactly or says why not.

Design rules:

1. The engine is dumb and honest. It never rescales, never reflows, never
   guesses. It exposes exactly the lines it was sent, in order, or faults.
2. Every frame is independently checksummed (CRC-16/CCITT-FALSE). A corrupt
   frame is dropped and NACKed by sequence number; it can never place wrong
   bits on paper.
3. Blank lines travel as SKIP runs, not as 640 zero bytes, because most office
   pages are mostly blank and the first transport is USB Full Speed.
4. A JOB_END frame carries a whole-page CRC so truncated or reordered jobs
   fail loudly at the end even if every individual frame looked fine.

Frame layout (little-endian):

    offset  size  field
    0       1     SOF = 0xA5
    1       1     type
    2       2     seq        (uint16, increments per frame, wraps)
    4       2     payload_len
    6       n     payload
    6+n     2     crc16 over bytes 1 .. 6+n-1 (type through payload)

Frame types:

    0x01 JOB_START  payload: version(1)=1, dpi(2), width_px(2), total_lines(2), flags(1)=0
    0x02 LINE       payload: line_index(2), row bytes (ceil(width_px/8))
    0x03 SKIP       payload: start_line(2), count(2)   -- lines are all-white
    0x04 JOB_END    payload: lines_covered(2), page_crc16(2)
    0x10 ACK        payload: seq_acked(2), credit(1)   -- engine -> host
    0x11 NACK       payload: seq_refused(2), error(1)  -- engine -> host
"""

from dataclasses import dataclass
import struct

from .engine_math import EngineTargets, line_rate_lps, lines_down, page_bytes

SOF = 0xA5
T_JOB_START = 0x01
T_LINE = 0x02
T_SKIP = 0x03
T_JOB_END = 0x04
T_ACK = 0x10
T_NACK = 0x11

ERR_CRC = 0x01
ERR_ORDER = 0x02
ERR_OVERFLOW = 0x03
ERR_COVERAGE = 0x04
ERR_PAGE_CRC = 0x05

FRAME_OVERHEAD_BYTES = 8  # SOF + type + seq + len + crc16


def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _frame(frame_type: int, seq: int, payload: bytes) -> bytes:
    body = struct.pack("<BHH", frame_type, seq & 0xFFFF, len(payload)) + payload
    return bytes([SOF]) + body + struct.pack("<H", crc16_ccitt(body))


def encode_page(rows: list[bytes], dpi: int, width_px: int) -> list[bytes]:
    """Encode a full page of packed 1-bpp rows into OFP1 frames.

    Runs of all-white (all-zero) rows become SKIP frames. Returns the frame
    list; page CRC covers every row's bytes in order, blank rows included.
    """
    row_len = page_bytes(width_px, 1)
    for i, row in enumerate(rows):
        if len(row) != row_len:
            raise ValueError(f"row {i} is {len(row)} bytes, expected {row_len}")
    frames: list[bytes] = []
    seq = 0

    def emit(frame_type: int, payload: bytes) -> None:
        nonlocal seq
        frames.append(_frame(frame_type, seq, payload))
        seq += 1

    emit(T_JOB_START, struct.pack("<BHHHB", 1, dpi, width_px, len(rows), 0))
    page_crc = 0xFFFF
    line = 0
    while line < len(rows):
        if not any(rows[line]):
            start = line
            while line < len(rows) and not any(rows[line]):
                page_crc = crc16_ccitt(rows[line], page_crc)
                line += 1
            emit(T_SKIP, struct.pack("<HH", start, line - start))
        else:
            page_crc = crc16_ccitt(rows[line], page_crc)
            emit(T_LINE, struct.pack("<H", line) + rows[line])
            line += 1
    emit(T_JOB_END, struct.pack("<HH", len(rows), page_crc))
    return frames


@dataclass
class DecodeResult:
    complete: bool
    rows: list[bytes]
    acks: list[tuple[int, int]]      # (seq, credit)
    nacks: list[tuple[int, int]]     # (seq, error code)
    error: str | None = None


class EngineDecoder:
    """Reference engine-side decoder: a byte-stream state machine.

    Feed it arbitrary chunks; it frames, CRC-checks, and reconstructs the
    page. Corrupt frames are NACKed and dropped without corrupting output.
    """

    def __init__(self) -> None:
        self._buf = bytearray()
        self._rows: list[bytes | None] = []
        self._row_len = 0
        self._total_lines = 0
        self._next_line = 0
        self._started = False
        self._page_crc = 0xFFFF
        self._declared: tuple[int, int] | None = None
        self.acks: list[tuple[int, int]] = []
        self.nacks: list[tuple[int, int]] = []
        self.error: str | None = None

    def feed(self, data: bytes) -> None:
        self._buf.extend(data)
        while self.error is None:
            frame = self._next_frame()
            if frame is None:
                return
            self._handle(*frame)

    def _next_frame(self) -> tuple[int, int, bytes] | None:
        buf = self._buf
        while buf and buf[0] != SOF:
            buf.pop(0)  # resync: discard garbage between frames
        if len(buf) < 6 + 2:
            return None
        frame_type, seq, length = struct.unpack("<BHH", bytes(buf[1:6]))
        total = 6 + length + 2
        if len(buf) < total:
            return None
        body = bytes(buf[1:6 + length])
        (crc,) = struct.unpack("<H", bytes(buf[6 + length:total]))
        del buf[:total]
        if crc16_ccitt(body) != crc:
            self.nacks.append((seq, ERR_CRC))
            return self._next_frame()
        return frame_type, seq, body[5:]

    def _fault(self, seq: int, code: int, message: str) -> None:
        self.nacks.append((seq, code))
        self.error = message

    def _accept_line(self, index: int, row: bytes, seq: int) -> bool:
        if index != self._next_line:
            self._fault(seq, ERR_ORDER, f"line {index} out of order, expected {self._next_line}")
            return False
        if index >= self._total_lines:
            self._fault(seq, ERR_OVERFLOW, f"line {index} beyond declared {self._total_lines}")
            return False
        self._rows[index] = row
        self._page_crc = crc16_ccitt(row, self._page_crc)
        self._next_line = index + 1
        return True

    def _handle(self, frame_type: int, seq: int, payload: bytes) -> None:
        if frame_type == T_JOB_START:
            _version, _dpi, width_px, total_lines, _flags = struct.unpack("<BHHHB", payload)
            self._row_len = page_bytes(width_px, 1)
            self._total_lines = total_lines
            self._rows = [None] * total_lines
            self._next_line = 0
            self._page_crc = 0xFFFF
            self._started = True
            self.acks.append((seq, 1))
        elif frame_type == T_LINE and self._started:
            (index,) = struct.unpack("<H", payload[:2])
            if self._accept_line(index, payload[2:], seq):
                self.acks.append((seq, 1))
        elif frame_type == T_SKIP and self._started:
            start, count = struct.unpack("<HH", payload)
            blank = bytes(self._row_len)
            for index in range(start, start + count):
                if not self._accept_line(index, blank, seq):
                    return
            self.acks.append((seq, 1))
        elif frame_type == T_JOB_END and self._started:
            covered, page_crc = struct.unpack("<HH", payload)
            if covered != self._next_line or any(r is None for r in self._rows):
                self._fault(seq, ERR_COVERAGE, "job ended with uncovered lines")
            elif page_crc != self._page_crc:
                self._fault(seq, ERR_PAGE_CRC, "page CRC mismatch")
            else:
                self._declared = (covered, page_crc)
                self.acks.append((seq, 1))

    def result(self) -> DecodeResult:
        complete = self._declared is not None and self.error is None
        rows = [r for r in self._rows if r is not None] if complete else []
        return DecodeResult(complete, rows, self.acks, self.nacks, self.error)


def transport_budget(target: EngineTargets | None = None) -> dict:
    """Can the first transport actually feed the engine? Honest numbers.

    Worst case is a page where every line carries toner (no SKIP wins):
    each line costs one full LINE frame at the engine line rate.
    """
    t = target or EngineTargets()
    row_len = page_bytes(t.led_pixels, 1)
    line_frame_bytes = FRAME_OVERHEAD_BYTES + 2 + row_len
    rate = line_rate_lps(t)
    worst_mbit_s = line_frame_bytes * 8 * rate / 1_000_000.0
    # USB Full Speed bulk ceiling: 19 x 64-byte packets per 1 ms frame.
    usb_fs_bulk_ceiling_mbit_s = 19 * 64 * 8 * 1000 / 1_000_000.0
    utilization = worst_mbit_s / usb_fs_bulk_ceiling_mbit_s
    letter_lines = lines_down(t.letter_length_mm, t.dpi)
    hiccup_ms = 10.0
    lines_per_hiccup = rate * hiccup_ms / 1000.0
    ring_lines = 32
    return {
        "line_frame_bytes": line_frame_bytes,
        "frame_overhead_fraction": (FRAME_OVERHEAD_BYTES + 2) / line_frame_bytes,
        "line_rate_lps": rate,
        "worst_case_required_mbit_s": worst_mbit_s,
        "usb_fs_bulk_ceiling_mbit_s": usb_fs_bulk_ceiling_mbit_s,
        "usb_fs_utilization_worst_case": utilization,
        "usb_fs_is_marginal": utilization > 0.7,
        # JOB_START payload 8 B, SKIP payload 4 B, JOB_END payload 4 B.
        "blank_letter_page_bytes_on_wire": 3 * FRAME_OVERHEAD_BYTES + 8 + 4 + 4,
        "solid_letter_page_bytes_on_wire": line_frame_bytes * letter_lines
        + 2 * FRAME_OVERHEAD_BYTES + 8 + 4,
        "host_hiccup_tolerance_target_ms": hiccup_ms,
        "lines_consumed_during_hiccup": lines_per_hiccup,
        "recommended_engine_ring_buffer_lines": ring_lines,
        "recommended_engine_ring_buffer_bytes": ring_lines * row_len,
        "ring_buffer_covers_hiccup": ring_lines > lines_per_hiccup,
        "verdict": (
            "USB Full Speed can only feed a worst-case page at "
            f"{utilization:.0%} of its bulk ceiling with zero competing traffic; "
            "spec USB High Speed (or engine-side page RAM) for production, "
            "keep FS as the degraded 8 ppm service mode."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(transport_budget(), indent=2))
