# SC_Slicer 可移植命令入口。默认 doctor 只读自检。
PY ?= python3
FORGE ?= forge

.PHONY: doctor install build test test-stage2 test-stage3 test-pipeline e2e metrics metrics-sync

doctor:
	./scripts/doctor.sh

install:
	./scripts/bootstrap.sh install

build:
	cargo build --release

test: test-stage2 test-stage3 test-pipeline
	cargo test

test-stage2:
	cd tools/report_constraints_v2 && $(PY) -m unittest discover -s tests -q

test-stage3:
	cd tools/stage3 && $(PY) -m unittest discover -s tests -q

test-pipeline:
	cd tools/pipeline && $(PY) -m unittest discover -s tests -q

e2e:
	./run.sh

metrics:
	cd tools/stage3/evaluation/metrics && $(PY) unified_metrics.py
	cd tools/stage3/evaluation/metrics && $(PY) independence_report.py

metrics-sync:
	$(PY) main.py stage3 metrics-sync
