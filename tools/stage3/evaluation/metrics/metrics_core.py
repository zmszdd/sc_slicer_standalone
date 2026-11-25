"""Single source of truth for the four-metric math and confidence intervals.

Every authoritative report derives recall / precision / F1 / completion
through these functions, and every report exposes Wilson 95% CI through
``wilson_ci`` so a point estimate is never presented without its interval.
"""
from __future__ import annotations

import math
import random

VALID_STATES = {'valid', 'fixed', 'wontfix'}
INVALID_STATE = 'invalid'


def f1(precision: float | None, recall: float) -> float | None:
    if precision is None or recall is None or (precision + recall) == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def recall(tp: int, positives: int) -> float:
    return tp / positives if positives else 0.0


def precision_rate(tp: int, predicted_positive: int) -> float:
    return tp / predicted_positive if predicted_positive else 0.0


def accuracy_rate(tp: int, fp: int, fn: int, tn: int) -> float:
    """Standard case-level accuracy from one frozen confusion matrix."""
    total = tp + fp + fn + tn
    return (tp + tn) / total if total else 0.0


def completion_rate(done: int, total: int) -> float:
    return done / total if total else 0.0


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    """Wilson score interval for a binomial proportion.

    Returns ``(low, high)`` or ``(None, None)`` for a zero-size denominator.
    """
    if n <= 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / denom, (centre + margin) / denom


def ci_interval(k: int, n: int, z: float = 1.96) -> dict:
    low, high = wilson_ci(k, n, z)
    return {
        'low': round(low, 4) if low is not None else None,
        'high': round(high, 4) if high is not None else None,
    }


def project_of(case: str) -> str:
    """Project prefix is everything before the first ``__`` separator."""
    return case.split('__')[0]


def cluster_bootstrap_ci(rows: list[dict], metric_fn, *,
                         cluster_key: str = 'project', samples: int = 2000,
                         seed: int = 13) -> tuple[float | None, float | None]:
    """Cluster-bootstrap CI for correlated findings from the same project.

    ``metric_fn`` receives a resampled list of rows and returns a scalar.  The
    same project is always resampled as one unit, so dozens of findings from
    one project cannot masquerade as independent observations.
    """
    if not rows:
        return None, None
    clusters: dict[str, list[dict]] = {}
    for row in rows:
        key = row.get(cluster_key)
        if key is None:
            key = project_of(str(row.get('case') or ''))
        clusters.setdefault(str(key), []).append(row)
    keys = sorted(clusters)
    if not keys:
        return None, None
    rng = random.Random(seed)
    values = []
    for _ in range(max(1, samples)):
        selected = [rng.choice(keys) for _ in keys]
        resampled = [row for key in selected for row in clusters[key]]
        value = metric_fn(resampled)
        if value is not None:
            values.append(float(value))
    if not values:
        return None, None
    values.sort()
    low = values[int(0.025 * (len(values) - 1))]
    high = values[int(0.975 * (len(values) - 1))]
    return low, high


def split_positives_negatives(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    positives = [r for r in rows if r.get('validity') in VALID_STATES]
    negatives = [r for r in rows if r.get('validity') == INVALID_STATE]
    return positives, negatives


def confusion_metrics(*, tp: int, fp: int, fn: int, tn: int,
                      fp_vuln: int | None = None,
                      fp_impact_insufficient: int = 0,
                      automatic_tp: int | None = None) -> dict:
    """Compute the full four-metric block from one confusion matrix.

    ``fp`` is the raw judge-invalid reproduced count (consistency口径);
    ``fp_vuln`` is the vulnerability-level FP after removing impact-
    insufficient cases.  ``automatic_tp`` (assert-injection reproductions
    only, excluding reference-patch) yields ``recall_automatic``.
    """
    if fp_vuln is None:
        fp_vuln = max(0, fp - fp_impact_insufficient)
    precision_consistency = precision_rate(tp, tp + fp)
    precision_vuln = precision_rate(tp, tp + fp_vuln)
    recall_e2e = recall(tp, tp + fn)
    accuracy = accuracy_rate(tp, fp, fn, tn)
    f1_consistency = f1(precision_consistency, recall_e2e)
    f1_vuln = f1(precision_vuln, recall_e2e)

    automatic = automatic_tp if automatic_tp is not None else None
    recall_auto = recall(automatic, tp + fn) if automatic is not None else None
    f1_auto = f1(precision_vuln, recall_auto) if recall_auto is not None else None

    return {
        'accuracy': round(accuracy, 4),
        'recall': round(recall_e2e, 4),
        'recall_automatic': round(recall_auto, 4) if recall_auto is not None else None,
        'precision': round(precision_vuln, 4),
        'precision_consistency': round(precision_consistency, 4),
        'precision_vuln': round(precision_vuln, 4),
        'f1': round(f1_vuln, 4) if f1_vuln is not None else None,
        'f1_consistency': round(f1_consistency, 4) if f1_consistency is not None else None,
        'f1_vuln': round(f1_vuln, 4) if f1_vuln is not None else None,
        'f1_automatic': round(f1_auto, 4) if f1_auto is not None else None,
    }
