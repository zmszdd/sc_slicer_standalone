"""Replay frozen semantic-v3.1 holdout artifacts and preliminary ratings; no calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
sys.path.insert(0, str(MODULE))

import report_only as r
from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from semantic_core import validate_elements, validate_formalization
from verify_semantic import verify

DIMENSIONS = ("scope_actors", "preconditions", "safety_intent", "formal_I", "core_V", "qualifiers_coverage")
VALUES = ("pass", "partial", "fail", "not_evaluable")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    frozen = json.loads((HERE / "FROZEN_INPUTS.json").read_text())
    ratings = json.loads((HERE / "ratings.json").read_text())
    manifest = json.loads((HERE / "cases.json").read_text())
    for path, expected in ((HERE / "REFERENCE.md", frozen["reference_sha256"]),
                           (HERE / "cases.json", frozen["cases_sha256"]),
                           (MODULE / 'prompts/versions/semantic_prompts_v31.py',
                            frozen["prompt_sha256"])):
        if sha(path) != expected:
            raise ValueError(f"frozen input changed: {path.name}")
    if ratings["reference_sha256"] != frozen["reference_sha256"]:
        raise ValueError("ratings/reference mismatch")

    ids = [row["id"] for row in manifest["cases"]]
    reviewed = {row["id"]: row for row in ratings["cases"]}
    if set(reviewed) != set(ids) or len(reviewed) != len(ids):
        raise ValueError("ratings must cover all cases once")
    root = MODULE / "results" / "semantic" / "prompt_v31_holdout_model_01"
    batch = json.loads((root / "batch-summary.json").read_text())
    results, usage = [], []
    for case_id in ids:
        manual = reviewed[case_id]
        if set(manual["ratings"]) != set(DIMENSIONS) or any(v not in VALUES for v in manual["ratings"].values()):
            raise ValueError("invalid rating")
        directory = root / case_id
        provenance = json.loads((directory / "provenance.json").read_text())
        if provenance.get("prompt_version") != frozen["prompt_version"]:
            raise ValueError(f"{case_id}: wrong prompt version")
        raw = (directory / "original-report").read_bytes()
        text = (directory / "extraction-input.txt").read_text()
        if r.sha(raw) != provenance["report_sha256"] or r.sha(text.encode()) != provenance["report_input_sha256"]:
            raise ValueError(f"{case_id}: input hash mismatch")
        if text != r.prose_only(json.loads(raw)["body"]):
            raise ValueError(f"{case_id}: prose mismatch")
        catalog = json.loads((directory / "evidence-catalog.json").read_text())
        if catalog != build_catalog(text):
            raise ValueError(f"{case_id}: catalog mismatch")

        elements_ok = False
        if (directory / "elements-ids.json").exists():
            raw_elements = json.loads((directory / "elements-ids.json").read_text())
            if sha(directory / "neural-elements/model-claim.json") != manual["elements_candidate_sha256"]:
                raise ValueError(f"{case_id}: elements candidate changed")
            elements = hydrate_elements(raw_elements, catalog, text)
            if elements != json.loads((directory / "elements.json").read_text()):
                raise ValueError(f"{case_id}: elements hydration mismatch")
            validate_elements(elements, text)
            elements_ok = True

        formal_error = None
        formal_replay = None
        if (directory / "formalization-ids.json").exists():
            if not elements_ok:
                raise ValueError(f"{case_id}: formalization without elements")
            if sha(directory / "neural-formalization/model-claim.json") != manual["formalization_candidate_sha256"]:
                raise ValueError(f"{case_id}: formalization candidate changed")
            raw_formal = json.loads((directory / "formalization-ids.json").read_text())
            formal = hydrate_formalization(raw_formal, catalog, text)
            if formal != json.loads((directory / "formalization.json").read_text()):
                raise ValueError(f"{case_id}: formalization hydration mismatch")
            try:
                validate_formalization(formal, elements, text)
            except ValueError as exc:
                formal_error = str(exc)
            if (directory / "constraints.json").exists():
                if formal_error:
                    raise ValueError(f"{case_id}: invalid formalization reached bundle")
                formal_replay = verify(directory)

        for path in directory.glob("neural-*/model-usage.json"):
            usage.extend(json.loads(path.read_text())["steps"])
        status = json.loads((directory / "status.json").read_text())
        if formal_error != status.get("error") and status.get("error_type") == "ValueError":
            raise ValueError(f"{case_id}: formal rejection mismatch")
        results.append({**manual, "pipeline_status": status,
                        "elements_grounding_replayed": elements_ok,
                        "formal_validation_error_replayed": formal_error,
                        "formal_pipeline_replay": formal_replay,
                        "complete_semantic_pass": all(v == "pass" for v in manual["ratings"].values())})

    batch_rows = {row["case_id"]: row["status"] for row in batch["results"]}
    if any(batch_rows[row["id"]] != row["pipeline_status"] for row in results):
        raise ValueError("batch/status mismatch")
    counts = {d: {v: sum(row["ratings"][d] == v for row in results) for v in VALUES} for d in DIMENSIONS}
    extraction_dims = tuple(d for d in DIMENSIONS if d != "formal_I")
    extraction_pass = sum(counts[d]["pass"] for d in extraction_dims)
    return {
        "schema_version": "prompt-v31-holdout-evaluation/1",
        "prompt_version": frozen["prompt_version"],
        "reviewer": ratings["reviewer"],
        "reference_status": ratings["reference_status"],
        "distinct_reports": len(ids),
        "actual_model_invocations": sum(row["pipeline_status"]["external_model_invocations"] for row in results),
        "evaluation_model_invocations": 0,
        "metric_counts": counts,
        "preliminary_extraction_strict_pass_cells": extraction_pass,
        "preliminary_extraction_total_cells": len(ids) * len(extraction_dims),
        "preliminary_extraction_strict_pass_percentage": 100 * extraction_pass / (len(ids) * len(extraction_dims)),
        "preliminary_formal_I_pass_count": counts["formal_I"]["pass"],
        "preliminary_formal_I_pass_percentage": 100 * counts["formal_I"]["pass"] / len(ids),
        "elements_completed_count": sum(row["elements_grounding_replayed"] for row in results),
        "formal_response_count": sum(row["formal_validation_error_replayed"] is not None or row["formal_pipeline_replay"] is not None for row in results),
        "formal_pipeline_completed_count": sum(row["formal_pipeline_replay"] is not None for row in results),
        "timeout_case_count": sum(row["pipeline_status"].get("error_type") == "TimeoutExpired" for row in results),
        "complete_semantic_pass_count": sum(row["complete_semantic_pass"] for row in results),
        "recorded_usage_file_count": len(usage),
        "reported_total_tokens_partial": sum(step["tokens"]["total"] for step in usage),
        "reported_cost_partial_not_verified_bill": round(sum(step["cost"] for step in usage), 8),
        "general_accuracy_percentage": None,
        "limitations": [
            "Five deliberately selected reports; not a random population sample.",
            "Assistant-preliminary reference/grading, not user or expert ground truth.",
            "The extraction percentage is a qualitative pass-cell rate, not report accuracy.",
            "Two timed-out calls have no usage file; reported token/cost totals are incomplete.",
            "Different reports and model-service behavior prevent causal comparison with v3.",
            "No code transition T or PoC/report consistency verdict.",
        ],
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write new archive; never overwrite")
    args = parser.parse_args()
    rendered = json.dumps(evaluate(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(rendered)
    print(rendered, end="")
