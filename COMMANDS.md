# Commands

## Run everything from a downloaded zip

```bash
cd "$HOME/Downloads" && rm -rf openframe_printer_newbuild_v2 && unzip -o openframe_printer_newbuild_v2.zip && cd openframe_printer_newbuild_v2 && python3 -m venv .venv && . .venv/bin/activate && python -m pip install --upgrade pip && python -m openframe_printer.demo && python scripts/smoke_test.py
```

## Regenerate only the design report

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.design_report
```

## Print the core engine math to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.engine_math
```

## Print the motion model to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.motion_model
```

## Print the fuser model summary to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.fuser_model
```

## Print the future inkjet/nozzle math to the terminal

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.nozzle_math
```

## Print the Rev B electrophotography physics guardrails

```bash
cd "$HOME/Downloads/openframe_printer_newbuild_v2" && . .venv/bin/activate && python -m openframe_printer.ep_physics
```
