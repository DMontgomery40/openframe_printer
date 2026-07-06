# RFQ 01: LED exposure bar

Document: OpenFrame M1 module RFQ  
Module ID: OF-M1-LEDBAR  
Revision: G, aligned to OpenFrame M1 Rev G  
Referenced platform docs: `docs/18_led_exposure_bar_spec.md`, `docs/51_revG_ledbar_optical_mtf.md`, `hardware/design_targets_revA.yaml`

## 1. What we are buying

A stationary monochrome LED exposure bar suitable for a 600 dpi dry electrophotographic printer.

## 2. Required ratings

| Parameter | Requirement |
|---|---:|
| Active pixels | 5120 |
| Pixel pitch | 42.333 µm |
| Active width | 216.747 mm |
| Wavelength starting target | 780 nm |
| Acceptable wavelength disclosure range | 660-780 nm |
| Line payload | 640 bytes at 1 bpp |
| Line period at engine target | 682.8 µs |
| Recommended shift clock support | at least 20 MHz equivalent |
| Thermal monitor | NTC or equivalent analog temperature readback |
| Output enable | hardware-gated OE input required |
| Optical MTF at OPC plane | >=0.35 at 12 lp/mm |
| Equivalent spot FWHM shortcut | <=45 µm if MTF not directly supplied |
| One-pixel optical crosstalk | <=15% at OPC plane |

## 3. Interface preference

Preferred electrical interface:

- differential clock,
- two differential data lanes,
- differential latch,
- hardware OE,
- switched 5 V LED rail,
- 3.3 V logic rail,
- analog temp monitor.

## 4. Deliverables requested with quote

1. Mechanical outline drawing.
2. Pixel pitch and active width tolerance.
3. Electrical timing diagram.
4. LED wavelength and optical power uniformity data.
5. Recommended exposure energy range for compatible OPC materials.
6. Measured MTF at the OPC plane, or measured spot/FWHM data sufficient to reproduce `out/v2_optical_mtf_budget.json`.
7. Sample pricing at 5, 25, 250, and 2500 pieces.
8. Confirmation that interface drawings may be published in an open service manual.

## 5. Acceptance tests

| Test | Pass criterion |
|---|---|
| Timing | shift and latch one 640-byte line within 25% of 682.8 µs |
| Uniformity | supplier states correction method or max uncorrected variation |
| Safety gate | OE disabled when hardware gate removed |
| Thermal | temp monitor responds during one-hour timing run |
| Optical MTF | MTF >=0.35 at 12 lp/mm at the OPC plane, or equivalent FWHM/crosstalk gate passes |
