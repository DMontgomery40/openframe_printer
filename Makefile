.PHONY: demo report test clean

demo:
	python -m openframe_printer.demo

report:
	python -m openframe_printer.design_report

test:
	python scripts/smoke_test.py

clean:
	rm -rf out .venv __pycache__ openframe_printer/__pycache__ scripts/__pycache__
