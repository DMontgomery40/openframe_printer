# Commands

## Run everything from a downloaded Rev F zip

```bash
cd "$HOME/Downloads" && rm -rf openframe_printer_newbuild_v2 && unzip -o openframe_printer_newbuild_v2_research_revF.zip && cd openframe_printer_newbuild_v2 && python3 -m venv .venv && . .venv/bin/activate && python -m pip install --upgrade pip && python -m openframe_printer.demo && python -m openframe_printer.design_report && python scripts/smoke_test.py && python scripts/model_tests.py
```

## Regenerate only the design report

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.design_report
```

## Run the generated-artifact smoke gate

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python scripts/smoke_test.py
```

## Run the focused model suite

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python scripts/model_tests.py
```

## Print the core engine math to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.engine_math
```

## Print the motion model to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.motion_model
```

## Print the fuser warm-up model summary to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.fuser_model
```

## Print the fuser continuous paper-load balance

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python - <<'PY'
from pprint import pprint
from openframe_printer.fuser_power import fuser_power_summary
pprint(fuser_power_summary())
PY
```

## Print the Rev F halftone floor gate

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python - <<'PY'
from pprint import pprint
from openframe_printer.halftone import halftone_floor_gate
pprint(halftone_floor_gate())
PY
```

## Print the Rev F interlock fault analysis

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python - <<'PY'
from pprint import pprint
from openframe_printer.interlock_faults import interlock_fault_summary
pprint(interlock_fault_summary())
PY
```

## Print the Rev F LED thermal feed-forward summary

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python - <<'PY'
from pprint import pprint
from openframe_printer.led_thermal import led_thermal_summary
pprint(led_thermal_summary())
PY
```

## Print the Rev B electrophotography physics guardrails

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.ep_physics
```
