"""Replay frozen v3/v3.2 A/B outputs and preliminary ratings; no model calls."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
sys.path.insert(0, str(MODULE))
from verify_semantic import verify

VALUES = {"pass", "partial", "fail", "not_evaluable"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate():
    frozen = json.loads((HERE / "FROZEN_INPUTS.json").read_text())
    cases = json.loads((HERE / "cases.json").read_text())
    ratings = json.loads((HERE / "ratings.json").read_text())
    if sha(HERE / "REFERENCE.md") != frozen["reference_sha256"]:
        raise ValueError("frozen reference changed")
    if sha(HERE / "cases.json") != frozen["cases_sha256"]:
        raise ValueError("frozen cases changed")
    for version, name in (("semantic-v3", "semantic_prompts.py"),
                          ("semantic-v3.2", "semantic_prompts_v32.py")):
        if sha(MODULE / 'prompts/versions' / name) != frozen["prompt_sha256"][version]:
            raise ValueError("frozen prompt changed: " + version)
    ids = [row["id"] for row in cases["cases"]]
    outputs = {"semantic-v3": MODULE / "results/semantic/prompt_v32_ab_01_v3",
               "semantic-v3.2": MODULE / "results/semantic/prompt_v32_ab_01_v32"}
    versions = {}
    for version, root in outputs.items():
        batch = json.loads((root / "batch-summary.json").read_text())
        if batch["prompt_version"] != version:
            raise ValueError("batch prompt mismatch")
        status = {row["case_id"]: row["status"] for row in batch["results"]}
        reviewed = {row["id"]: row for row in ratings["versions"][version]}
        if set(status) != set(ids) or set(reviewed) != set(ids):
            raise ValueError("case coverage mismatch")
        replayed = 0
        direct_gate_pass = 0
        usage_steps = []
        counts = {d: {v: 0 for v in VALUES} for d in ratings["dimensions"]}
        for case_id in ids:
            row = reviewed[case_id]
            if set(row["ratings"]) != set(ratings["dimensions"]):
                raise ValueError("rating dimensions mismatch")
            for dimension, value in row["ratings"].items():
                if value not in VALUES:
                    raise ValueError("invalid rating")
                counts[dimension][value] += 1
            directory = root / case_id
            if "elements_candidate_sha256" in row:
                if sha(directory / "neural-elements/model-claim.json") != row["elements_candidate_sha256"]:
                    raise ValueError("elements candidate changed")
            if "formalization_candidate_sha256" in row:
                if sha(directory / "neural-formalization/model-claim.json") != row["formalization_candidate_sha256"]:
                    raise ValueError("formal candidate changed")
            if (directory / "constraints.json").exists():
                verify(directory)
                replayed += 1
                bundle = json.loads((directory / "constraints.json").read_text())
                direct_gate_pass += all(c["semantic_relationship"].get("direct_counterexample_status") == "passed"
                                        for c in bundle["claims"])
            for usage in directory.glob("neural-*/model-usage.json"):
                usage_steps.extend(json.loads(usage.read_text())["steps"])
        strict_pass = sum(counts[d]["pass"] for d in ratings["dimensions"])
        versions[version] = {
            "case_count": len(ids),
            "attempted_model_invocations": sum(x["external_model_invocations"] for x in status.values()),
            "timeout_case_count": sum(x.get("error_type") == "TimeoutExpired" for x in status.values()),
            "formal_pipeline_completed_count": replayed,
            "symbolic_direct_counterexample_gate_pass_count": direct_gate_pass,
            "complete_all_dimension_pass_count": sum(all(v == "pass" for v in reviewed[x]["ratings"].values()) for x in ids),
            "rating_counts": counts,
            "preliminary_strict_pass_cells": strict_pass,
            "preliminary_total_cells": len(ids) * len(ratings["dimensions"]),
            "recorded_usage_step_count": len(usage_steps),
            "reported_tokens_for_completed_usage_steps": sum(x["tokens"]["total"] for x in usage_steps),
            "reported_cost_for_completed_usage_steps_not_verified_bill": round(sum(x["cost"] for x in usage_steps), 8)
        }
    return {
        "schema_version": "prompt-v32-ab-evaluation/1",
        "reference_status": ratings["reference_status"],
        "reviewer": ratings["reviewer"],
        "versions": versions,
        "general_accuracy_percentage": None,
        "conclusion": "v3.2 completed all pipelines and enforced the syntactic V/not-I relation, but P role purity and formal-I fidelity remain unresolved; no accuracy improvement is established.",
        "limitations": [
            "Three deliberately selected cases are not a population sample.",
            "Reference and grading are assistant-preliminary, not expert-confirmed.",
            "v3 timeouts prevent a complete paired semantic comparison.",
            "External service timing and stochastic generation confound prompt effects.",
            "The symbolic direct-counterexample gate is relative to generated I and cannot validate I semantics."
        ]
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
