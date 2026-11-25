# SC_Slicer 可移植命令入口。默认 doctor 只读自检。
PY ?= python3
FORGE ?= forge

.PHONY: doctor install build test test-stage2 test-stage3 test-pipeline test-code4rena e2e fmt lint protocol-check protocol-baseline verify prune-dry-run hygiene hygiene-apply metrics metrics-resample metrics-sync metrics-check mainline-status blind-status collect-stage3 eval-contract dev24 dev-current-mini locked-eval-check provider-check execution-preflight paper-evidence metric-alignment case-readiness effect-reaudit stage2-observability-audit stage2-preflight stage2-binding-candidate label-review

doctor:
	./scripts/doctor.sh

install:
	./scripts/bootstrap.sh install

build:
	cargo build --release

test: test-stage2 test-stage3 test-pipeline test-code4rena
	cargo test

test-stage2:
	cd tools/report_constraints_v2 && $(PY) -m unittest discover -s tests -q

test-stage3:
	cd tools/stage3 && $(PY) -m unittest discover -s tests -q

test-pipeline:
	cd tools/pipeline && $(PY) -m unittest discover -s tests -q

test-code4rena:
	cd scripts/code4rena && $(PY) -m unittest discover -s tests -q

e2e:
	./run.sh

fmt:
	cargo fmt

lint:
	cargo clippy --all-targets --locked -- -D warnings

protocol-check:
	cd tools/stage3 && $(PY) -m lib.mainline_protocol --check

protocol-baseline:
	cd tools/stage3 && $(PY) -m lib.mainline_protocol --write

verify: doctor protocol-check lint
	git diff --check
	$(MAKE) test
	$(MAKE) metrics-check
	$(MAKE) e2e

prune-dry-run:
	./scripts/prune_evaluation_artifacts.sh

hygiene:
	./scripts/cleanup_generated.sh

hygiene-apply:
	./scripts/cleanup_generated.sh --apply

metrics:
	cd tools/stage3/evaluation/metrics && $(PY) current_denominator.py
	cd tools/stage3/evaluation/metrics && $(PY) mainline_metrics.py
	cd tools/stage3/evaluation/metrics && $(PY) mainline_stage2_triage.py
	cd tools/stage3/evaluation/metrics && $(PY) mainline_backlog.py
	cd tools/stage3/evaluation/metrics && $(PY) case_readiness.py
	cd tools/stage3/evaluation/metrics && $(PY) label_review_gate.py
	cd tools/stage3/evaluation/metrics && $(PY) effect_witness_reaudit.py
	cd tools/stage3 && $(PY) -m cli.stage3_locked_eval --strict >/dev/null
	cd tools/stage3/evaluation/metrics && $(PY) paper_evidence_report.py
	cd tools/stage3/evaluation/metrics && $(PY) metric_alignment_report.py

# Explicit escape hatch only. Reselecting cases invalidates the frozen
# denominator; use it only with a new protocol version and explicit approval.
metrics-resample:
	cd tools/stage3/evaluation/metrics && $(PY) sample_mainline.py --target-negatives 60 --seed 20261115 --official-negative-pool official_negative_pool_20261121.json
	$(MAKE) metrics

# Legacy/diagnostic metrics. Kept for auditability, not part of the mainline.
metrics-legacy:
	cd tools/stage3/evaluation/metrics && $(PY) fullset_metrics.py
	cd tools/stage3/evaluation/metrics && $(PY) unified_metrics.py
	cd tools/stage3/evaluation/metrics && $(PY) independence_report.py

metrics-sync:
	$(PY) main.py stage3 metrics-sync

metrics-check:
	cd tools/stage3 && $(PY) -m cli.stage3_metrics_sync --check

locked-eval-check:
	cd tools/stage3 && $(PY) -m cli.stage3_locked_eval --strict

provider-check:
	cd tools/stage3 && $(PY) -m evaluation.metrics.provider_probe

execution-preflight:
	cd tools/stage3 && $(PY) -m evaluation.metrics.execution_preflight $(ARGS)

paper-evidence:
	cd tools/stage3/evaluation/metrics && $(PY) paper_evidence_report.py

stage2-observability-audit:
	cd tools/stage3/evaluation/metrics && $(PY) stage2_observability_audit.py

metric-alignment:
	cd tools/stage3/evaluation/metrics && $(PY) metric_alignment_report.py

case-readiness:
	cd tools/stage3/evaluation/metrics && $(PY) case_readiness.py

stage2-preflight:
	$(PY) tools/stage3/evaluation/metrics/stage2_observability_preflight.py $(ARGS)

stage2-binding-candidate:
	$(PY) tools/stage3/evaluation/metrics/stage2_restatement_binding_candidate.py $(ARGS)

label-review:
	cd tools/stage3/evaluation/metrics && $(PY) label_review_gate.py

effect-reaudit:
	cd tools/stage3/evaluation/metrics && $(PY) effect_witness_reaudit.py

mainline-status:
	cd tools/stage3/evaluation/metrics && $(PY) mainline_status.py

blind-status:
	cd tools/stage3/evaluation/metrics && $(PY) blind_build.py
	cd tools/stage3/evaluation/metrics && $(PY) blind_data_audit.py
	cd tools/stage3/evaluation/metrics && $(PY) blind_stage3_summary.py
	cd tools/stage3/evaluation/metrics && $(PY) blind_metrics.py
	cd tools/stage3/evaluation/metrics && $(PY) mainline_status.py

collect-stage3:
	cd tools/stage3/evaluation/metrics && $(PY) collect_stage3_runs.py --prefix mainline_gate --out blind_stage3_eval_20261118.json

eval-contract:
	cd tools/stage3 && $(PY) evaluation/metrics/build_dev_24.py
	cd tools/stage3 && $(PY) evaluation/metrics/experiment_contract.py

dev24:
	cd tools/stage3 && $(PY) evaluation/metrics/run_dev_24.py

dev-current-mini:
	cd tools/stage3 && $(PY) evaluation/metrics/build_dev_current_mini.py
	cd tools/stage3 && $(PY) evaluation/metrics/run_dev_24.py \
		--manifest evaluation/frozen/dev_current_mini_20261120.json \
		--out evaluation/metrics/dev_current_mini_results.json \
		--run-id-prefix dev_current_mini --no-gate-exit \
		--concurrency 8 --timeout 900
	cd tools/stage3 && $(PY) evaluation/metrics/dev_current_metrics.py \
		--manifest evaluation/frozen/dev_current_mini_20261120.json
