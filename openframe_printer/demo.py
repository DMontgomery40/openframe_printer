from __future__ import annotations

import json
from pathlib import Path
from .engine_math import EngineTargets, design_calcs
from .raster import text_to_bitmap, write_pbm
from .design_report import build_report

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    sample = (ROOT / "examples" / "sample_page.txt").read_text(encoding="utf-8")
    bitmap = text_to_bitmap(sample, scale=3, margin=24)
    pbm = OUT / "openframe_m1_page.pbm"
    write_pbm(bitmap, pbm)

    calcs = design_calcs(EngineTargets())
    job_plan = {
        "protocol": "OFP1",
        "printer": "OpenFrame M1 newbuild-v2 Rev A",
        "page_raster_preview": "openframe_m1_page.pbm",
        "engine": {
            "technology": "monochrome dry electrophotographic LED",
            "process_speed_mm_s": calcs["process_speed_mm_s_letter"],
            "drum_rpm": calcs["drum_rpm"],
            "line_rate_lps": calcs["line_rate_lps_letter"],
            "line_period_us": calcs["line_period_us_letter"],
            "led_pixels": calcs["led_pixels"],
            "led_line_payload_bytes": calcs["led_line_payload_bytes"],
        },
        "safe_defaults": {
            "hv_enabled": False,
            "fuser_enabled": False,
            "led_output_enabled": False,
            "requires_cover_interlock": True,
            "is_donor_printer_conversion": False,
        },
    }
    (OUT / "openframe_m1_job_plan.json").write_text(json.dumps(job_plan, indent=2), encoding="utf-8")
    build_report()
    print("Generated:")
    for p in [pbm, OUT / "openframe_m1_job_plan.json", OUT / "v2_design_report.md"]:
        print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
