#!/usr/bin/env python3
"""全量 judge-anchored 四指标：对 judge_ground_truth 的每一行结算。

与 unified_metrics.py（手工 105 快照口径）不同，本脚本把分母换成
``judge_ground_truth.json`` 的全量判例：

* positives = validity in {valid, fixed, wontfix}
* negatives = validity == 'invalid'
* TP  = 任一 stage3 主线 run（auto 或 reference_patch）复现的 positive
* FN  = 未复现的 positive（含尚未构建/尚未运行的案例，诚实计为 FN）
* FP  = judge_anchor 已评测的 invalid 中复现的案例（vuln 口径剔除影响不足）
* TN  = 已评测 invalid 中未复现的案例
* completion = 有 stage3 主线 run 的 positive / 全量 positive

同时输出 Wilson 95% CI，避免把抽样噪声当稳定指标。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics_core import accuracy_rate, f1, recall as _recall, precision_rate

ROOT = HERE.parents[3]
RUNS = ROOT / 'tools' / 'stage3' / 'runs'
GT = HERE / 'judge_ground_truth.json'
JUDGE = HERE / 'judge_anchored_252.json'
POSITIVE_EVAL = HERE / 'positive_eval_252.json'
OUT_JSON = HERE / 'fullset_metrics.json'
OUT_MD = HERE / 'fullset_metrics.md'
VALID_STATES = {'valid', 'fixed', 'wontfix'}


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n == 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / denom, (centre + margin) / denom


def _is_reproduced_summary(summary: dict | None) -> bool:
    if not summary or summary.get('consistency_verdict') != 'violation_reproduced':
        return False
    exploit = ((summary.get('forge') or {}).get('exploit') or {})
    original_status = (exploit.get('original') or {}).get('status')
    patched_status = (exploit.get('patched') or {}).get('status')
    if original_status == 'Success' and patched_status == 'Failure':
        return True
    # Revert-DoS reference patches run in the opposite direction: the buggy
    # PoC reverts (original Failure) and the fixed code completes (patched
    # Success).  The pipeline marks this violation_reproduced only when the
    # case carries a reference patch, so honour that direction here too.
    return bool(summary.get('reference_patch_used')
                and original_status == 'Failure'
                and patched_status == 'Success')


class RunIndex:
    """Single-pass index of stage3 run dirs by case prefix."""

    def __init__(self, runs_dir: Path, case_names: set[str]):
        self.auto: dict[str, list[tuple[int, Path, str]]] = {}
        self.refpatch: dict[str, list[tuple[int, Path, str]]] = {}
        if not runs_dir.is_dir():
            return
        # longest case names first so the correct case wins prefix matching
        names = sorted(case_names, key=len, reverse=True)
        for entry in runs_dir.iterdir():
            if not entry.is_dir():
                continue
            name = entry.name
            # Regression re-runs are evaluation artifacts, not canonical
            # mainline runs.  They must not move the frozen dev snapshot.
            if name.startswith(('dev24__', 'smoke5__')):
                continue
            case = None
            for c in names:
                if name.startswith(c + '__'):
                    case = c
                    break
            if case is None:
                continue
            try:
                mtime = int(entry.stat().st_mtime)
            except OSError:
                continue
            if 'refpatch' in name:
                bucket = self.refpatch
            elif '_neg_' in name:
                continue
            else:
                bucket = self.auto
            bucket.setdefault(case, []).append((mtime, entry, name))
        for bucket in (self.auto, self.refpatch):
            for case in bucket:
                bucket[case].sort(key=lambda t: t[0], reverse=True)

    @staticmethod
    def _load(path: Path) -> dict | None:
        try:
            return json.loads((path / 'stage3-summary.json').read_text())
        except (OSError, json.JSONDecodeError):
            return None

    def latest_auto(self, case: str, claim_id: str | None = None) -> dict | None:
        for _mtime, path, _name in self.auto.get(case, []):
            if claim_id and claim_id not in _name:
                continue
            summary = self._load(path)
            if summary is not None:
                return summary
        return None

    def iter_auto(self, case: str,
                  claim_id: str | None = None) -> list[dict]:
        """All parseable automatic-run summaries for one case, newest first."""
        rows = []
        for _mtime, path, name in self.auto.get(case, []):
            if claim_id and claim_id not in name:
                continue
            summary = self._load(path)
            if summary is not None:
                rows.append(summary)
        return rows

    def latest_refpatch(self, case: str) -> dict | None:
        for _mtime, path, _name in self.refpatch.get(case, []):
            summary = self._load(path)
            if summary is not None:
                return summary
        return None

    def iter_refpatch(self, case: str) -> list[dict]:
        """All parseable reference-patch summaries for one case, newest first."""
        rows = []
        for _mtime, path, _name in self.refpatch.get(case, []):
            summary = self._load(path)
            if summary is not None:
                rows.append(summary)
        return rows

    def auto_reproduced(self, case: str, claim_ids: list[str]) -> bool:
        for cid in claim_ids:
            if _is_reproduced_summary(self.latest_auto(case, cid)):
                return True
        return _is_reproduced_summary(self.latest_auto(case))

    def refpatch_reproduced(self, case: str) -> bool:
        return _is_reproduced_summary(self.latest_refpatch(case))

    def done(self, case: str) -> bool:
        return bool(self.auto.get(case) or self.refpatch.get(case))


def _claim_map(positive_eval: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in positive_eval.get('cases', []):
        case = row.get('case')
        ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
        if case and ids:
            out[case] = ids
    return out


def _fmt(v: float | None) -> str:
    return f'{v:.4f}' if v is not None else 'n/a'


def main() -> dict:
    gt = json.loads(GT.read_text())
    judge = json.loads(JUDGE.read_text())
    positive_eval = json.loads(POSITIVE_EVAL.read_text())
    claims = _claim_map(positive_eval)
    pe_by_case = {row.get('case'): row for row in positive_eval.get('cases', [])}

    positives = [c for c in gt['cases'] if c.get('validity') in VALID_STATES]
    negatives = [c for c in gt['cases'] if c.get('validity') == 'invalid']
    index = RunIndex(RUNS, {c['case'] for c in positives} | {c['case'] for c in negatives})

    tp = 0
    tp_auto = 0
    tp_refpatch = 0
    done = 0
    status_counter: Counter[str] = Counter()
    tp_rows: list[dict] = []

    for case in positives:
        name = case['case']
        pe = pe_by_case.get(name)
        if pe is not None:
            # The frozen positive_eval snapshot is authoritative.  Scanning
            # later regression runs would silently move dev252 between reports.
            reproduced = int(pe.get('reproduced') or 0) > 0
            auto = int(pe.get('automatic_reproduced') or 0) > 0
            refpatch = int(pe.get('reference_patch_reproduced') or 0) > 0
            if pe.get('status') == 'done':
                done += 1
            if reproduced:
                tp += 1
                tp_auto += 1 if auto else 0
                tp_refpatch += 1 if refpatch else 0
                tp_rows.append({
                    'case': name,
                    'project': case.get('project'),
                    'route': 'reference_patch' if refpatch else 'auto',
                })
            else:
                status_counter[pe.get('status') or 'evaluated_not_reproduced'] += 1
            continue
        claim_ids = claims.get(name, [])
        auto = index.auto_reproduced(name, claim_ids)
        refpatch = index.refpatch_reproduced(name)
        repro = auto or refpatch
        if index.done(name):
            done += 1
        if repro:
            tp += 1
            tp_auto += 1 if auto else 0
            tp_refpatch += 1 if refpatch else 0
            tp_rows.append({
                'case': name,
                'project': case.get('project'),
                'route': 'reference_patch' if refpatch else 'auto',
            })
        else:
            status = ('not_evaluated' if not index.done(name)
                      else 'evaluated_not_reproduced')
            status_counter[status] += 1

    fp_raw = int(judge.get('fp_from_judge_invalid', 0))
    fp_impact_insufficient = int(judge.get('fp_impact_insufficient_count', 0))
    fp_vuln = max(0, fp_raw - fp_impact_insufficient)
    neg_evaluated = int(judge.get('judge_invalid_evaluated_total', 0))
    tn = max(0, neg_evaluated - fp_raw)
    neg_unevaluated = len(negatives) - neg_evaluated

    positives_total = len(positives)
    negatives_total = len(negatives)
    fn = positives_total - tp
    completion = done / positives_total if positives_total else 0.0
    recall_e2e = _recall(tp, positives_total)
    precision_vuln = precision_rate(tp, tp + fp_vuln)
    precision_consistency = precision_rate(tp, tp + fp_raw)
    f1_vuln = f1(precision_vuln, recall_e2e)
    f1_consistency = f1(precision_consistency, recall_e2e)
    recall_auto = _recall(tp_auto, positives_total)
    f1_auto = f1(precision_vuln, recall_auto)
    accuracy = accuracy_rate(tp, fp_raw, fn, tn)

    def ci(k: int, n: int):
        lo, hi = wilson_ci(k, n)
        return {'low': round(lo, 4) if lo is not None else None,
                'high': round(hi, 4) if hi is not None else None}

    out = {
        'schema_version': 'fullset-metrics/1',
        'denominator': {
            'note': 'judge_ground_truth 全量判例；不抽样、不排除未运行案例',
            'positives': positives_total,
            'negatives': negatives_total,
            'negative_evaluated': neg_evaluated,
            'negative_unevaluated': neg_unevaluated,
        },
        'confusion_matrix': {
            'tp': tp, 'fn': fn,
            'fp_raw': fp_raw, 'fp_vuln': fp_vuln,
            'fp_impact_insufficient': fp_impact_insufficient,
            'tn': tn,
            'positives': positives_total,
            'negatives_evaluated': neg_evaluated,
        },
        'metrics': {
            'completion_rate': round(completion, 4),
            'accuracy': round(accuracy, 4),
            'recall': round(recall_e2e, 4),
            'recall_automatic': round(recall_auto, 4),
            'precision_consistency': round(precision_consistency, 4),
            'precision_vuln': round(precision_vuln, 4),
            'f1_consistency': round(f1_consistency, 4) if f1_consistency is not None else None,
            'f1_vuln': round(f1_vuln, 4) if f1_vuln is not None else None,
            'f1_automatic': round(f1_auto, 4) if f1_auto is not None else None,
        },
        'confidence_intervals': {
            'completion_rate': ci(done, positives_total),
            'accuracy': ci(tp + tn, tp + fp_raw + fn + tn),
            'recall': ci(tp, positives_total),
            'recall_automatic': ci(tp_auto, positives_total),
            'precision_vuln': ci(tp, tp + fp_vuln),
            'precision_consistency': ci(tp, tp + fp_raw),
        },
        'coverage': {
            'positives_evaluated': done,
            'positives_unevaluated': positives_total - done,
            'tp_auto': tp_auto,
            'tp_reference_patch': tp_refpatch,
            'status_distribution': dict(status_counter),
        },
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    m = out['metrics']
    cim = out['confidence_intervals']
    def pct(x):
        return f'{x:.1%}' if x is not None else 'n/a'
    md = f"""# 全量四指标（judge_ground_truth 全量口径）

分母为 judge_ground_truth 全量判例：positive {positives_total} / negative {negatives_total}（已评测 {neg_evaluated}）。

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 完成率 | {pct(m['completion_rate'])} | {pct(cim['completion_rate']['low'])}–{pct(cim['completion_rate']['high'])} |
| 准确率 | {pct(m['accuracy'])} | {pct(cim['accuracy']['low'])}–{pct(cim['accuracy']['high'])} |
| 召回率（端到端） | {pct(m['recall'])} | {pct(cim['recall']['low'])}–{pct(cim['recall']['high'])} |
| 召回率（自动口径） | {pct(m['recall_automatic'])} | {pct(cim['recall_automatic']['low'])}–{pct(cim['recall_automatic']['high'])} |
| 精确率（vuln） | {pct(m['precision_vuln'])} | {pct(cim['precision_vuln']['low'])}–{pct(cim['precision_vuln']['high'])} |
| 精确率（consistency） | {pct(m['precision_consistency'])} | {pct(cim['precision_consistency']['low'])}–{pct(cim['precision_consistency']['high'])} |
| F1（vuln） | {_fmt(m['f1_vuln'])} | — |
| F1（consistency） | {_fmt(m['f1_consistency'])} | — |

混淆矩阵：TP {tp} / FN {fn} / FP_raw {fp_raw}（影响不足 {fp_impact_insufficient}，vuln {fp_vuln}）/ TN {tn}。

覆盖：positive 已评测 {done}/{positives_total}，未评测 {positives_total - done}；TP 中自动 {tp_auto}、参考补丁 {tp_refpatch}。

## 未复现 positive 状态分布

| 状态 | 数量 |
| --- | ---: |
"""
    for status, count in sorted(status_counter.items(), key=lambda kv: -kv[1]):
        md += f'| {status} | {count} |\n'
    md += '\n注：本表把“尚未构建/尚未运行”的 positive 诚实计为 FN，因此召回率显著低于 105 抽样口径。\n'
    OUT_MD.write_text(md)

    def p(v):
        return 'n/a' if v is None else f'{v}'
    print(f'全量四指标: completion={p(completion)} recall={p(recall_e2e)} '
          f'precision_vuln={p(precision_vuln)} f1_vuln={p(f1_vuln)}')
    print(f'分母: positive={positives_total} negative={negatives_total} '
          f'(neg_evaluated={neg_evaluated})')
    print(f'TP={tp} (auto={tp_auto}, refpatch={tp_refpatch}) FN={fn}')
    return out


if __name__ == '__main__':
    main()
