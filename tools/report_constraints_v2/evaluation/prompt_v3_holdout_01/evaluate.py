"""Replay the frozen semantic-v3 holdout evaluation; makes no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
sys.path.insert(0, str(MODULE))
for _d in (MODULE / 'lib', MODULE / 'cli'):
    _s = str(_d)
    if _s not in sys.path:
        sys.path.insert(0, _s)

import report_only as r
from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from semantic_core import validate_elements, validate_formalization
from verify_semantic import verify

DIMENSIONS = (
    "scope_actors", "preconditions", "safety_intent",
    "formal_I", "core_V", "qualifiers_coverage",
)
VALUES = ("pass", "partial", "fail", "not_evaluable")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    frozen = json.loads((HERE / "FROZEN_INPUTS.json").read_text())
    ratings = json.loads((HERE / "ratings.json").read_text())
    manifest = json.loads((HERE / "cases.json").read_text())
    if sha(HERE / "REFERENCE.md") != frozen["reference_sha256"]:
        raise ValueError("frozen reference changed")
    if sha(HERE / "cases.json") != frozen["cases_sha256"]:
        raise ValueError("frozen case manifest changed")
    if sha(MODULE / 'prompts/versions/semantic_prompts.py') != frozen["prompt_sha256"]:
        raise ValueError("evaluated prompt changed")
    if ratings["reference_sha256"] != frozen["reference_sha256"]:
        raise ValueError("ratings/reference mismatch")

    ids = [row["id"] for row in manifest["cases"]]
    reviewed = {row["id"]: row for row in ratings["cases"]}
    if set(reviewed) != set(ids) or len(reviewed) != len(ids):
        raise ValueError("ratings must cover each case exactly once")

    root = MODULE / "results" / "semantic" / "prompt_v3_holdout_model_01"
    batch = json.loads((root / "batch-summary.json").read_text())
    results = []
    recorded_usage = []
    for case_id in ids:
        manual = reviewed[case_id]
        if set(manual["ratings"]) != set(DIMENSIONS):
            raise ValueError("invalid rating dimensions")
        if any(value not in VALUES for value in manual["ratings"].values()):
            raise ValueError("invalid rating value")

        directory = root / case_id
        provenance = json.loads((directory / "provenance.json").read_text())
        raw = (directory / "original-report").read_bytes()
        text = (directory / "extraction-input.txt").read_text()
        if r.sha(raw) != provenance["report_sha256"]:
            raise ValueError(f"{case_id}: report snapshot mismatch")
        if r.sha(text.encode()) != provenance["report_input_sha256"]:
            raise ValueError(f"{case_id}: prose snapshot mismatch")
        if text != r.prose_only(json.loads(raw)["body"]):
            raise ValueError(f"{case_id}: prose derivation mismatch")
        catalog = json.loads((directory / "evidence-catalog.json").read_text())
        if catalog != build_catalog(text):
            raise ValueError(f"{case_id}: evidence catalog mismatch")

        elements_raw = json.loads((directory / "elements-ids.json").read_text())
        if sha(directory / "neural-elements" / "model-claim.json") != manual["elements_candidate_sha256"]:
            raise ValueError(f"{case_id}: elements candidate changed")
        if elements_raw != json.loads((directory / "neural-elements" / "model-claim.json").read_text()):
            raise ValueError(f"{case_id}: elements candidate archive mismatch")
        elements = hydrate_elements(elements_raw, catalog, text)
        if elements != json.loads((directory / "elements.json").read_text()):
            raise ValueError(f"{case_id}: hydrated elements mismatch")
        validate_elements(elements, text)

        for usage in directory.glob("neural-*/model-usage.json"):
            recorded_usage.extend(json.loads(usage.read_text())["steps"])

        status = json.loads((directory / "status.json").read_text())
        formal_replay = None
        if (directory / "formalization-ids.json").exists():
            if sha(directory / "neural-formalization" / "model-claim.json") != manual["formalization_candidate_sha256"]:
                raise ValueError(f"{case_id}: formalization candidate changed")
            formal_raw = json.loads((directory / "formalization-ids.json").read_text())
            formal = hydrate_formalization(formal_raw, catalog, text)
            if formal != json.loads((directory / "formalization.json").read_text()):
                raise ValueError(f"{case_id}: hydrated formalization mismatch")
            validate_formalization(formal, elements, text)
            formal_replay = verify(directory)

        results.append({
            **manual,
            "pipeline_status": status,
            "elements_grounding_replayed": True,
            "formal_pipeline_replay": formal_replay,
            "complete_semantic_pass": all(v == "pass" for v in manual["ratings"].values()),
        })

    batch_rows = {row["case_id"]: row["status"] for row in batch["results"]}
    if any(batch_rows[row["id"]] != row["pipeline_status"] for row in results):
        raise ValueError("batch/status mismatch")

    counts = {
        dimension: {value: sum(row["ratings"][dimension] == value for row in results)
                    for value in VALUES}
        for dimension in DIMENSIONS
    }
    extraction_dimensions = tuple(d for d in DIMENSIONS if d != "formal_I")
    extraction_cells = len(ids) * len(extraction_dimensions)
    extraction_passes = sum(counts[d]["pass"] for d in extraction_dimensions)
    formal_completed = sum(row["formal_pipeline_replay"] is not None for row in results)
    timeouts = sum(row["pipeline_status"].get("error_type") == "TimeoutExpired" for row in results)
    return {
        "schema_version": "prompt-v3-holdout-evaluation/1",
        "prompt_version": frozen["prompt_version"],
        "reviewer": ratings["reviewer"],
        "reference_status": ratings["reference_status"],
        "distinct_reports": len(ids),
        "actual_model_invocations": sum(row["pipeline_status"]["external_model_invocations"] for row in results),
        "evaluation_model_invocations": 0,
        "metric_counts": counts,
        "preliminary_extraction_strict_pass_cells": extraction_passes,
        "preliminary_extraction_total_cells": extraction_cells,
        "preliminary_extraction_strict_pass_percentage": 100 * extraction_passes / extraction_cells,
        "preliminary_formal_I_pass_count": counts["formal_I"]["pass"],
        "preliminary_formal_I_pass_percentage": 100 * counts["formal_I"]["pass"] / len(ids),
        "formal_pipeline_completed_count": formal_completed,
        "formal_pipeline_completed_percentage": 100 * formal_completed / len(ids),
        "timeout_case_count": timeouts,
        "complete_semantic_pass_count": sum(row["complete_semantic_pass"] for row in results),
        "recorded_usage_file_count": len(recorded_usage),
        "reported_total_tokens_partial": sum(step["tokens"]["total"] for step in recorded_usage),
        "reported_cost_partial_not_verified_bill": round(sum(step["cost"] for step in recorded_usage), 8),
        "general_accuracy_percentage": None,
        "limitations": [
            "Five deliberately selected short reports, not a random population sample.",
            "Reference and grading are assistant-preliminary, not user/expert-confirmed ground truth.",
            "The 88% extraction figure is a strict pass-cell rate over five qualitative dimensions, not report-level accuracy.",
            "Four formalization calls timed out and have no usage file; token/cost totals are incomplete.",
            "The old prompt baseline used different reports, so this is not a causal A/B comparison.",
            "No code transition T or PoC/report consistency verdict is evaluated here.",
        ],
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write a new metrics archive; never overwrite")
    args = parser.parse_args()
    rendered = json.dumps(evaluate(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(rendered)
    print(rendered, end="")
