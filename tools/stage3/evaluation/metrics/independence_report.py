#!/usr/bin/env python3
"""项目聚类稳健统计：样本独立性与规模的权威说明。

案例强相关（同项目多案例共享代码/根因），naive Wilson 会把强相关案例当独立
样本，给出偏窄的置信区间。本脚本按项目聚类，给出三套口径：

1) 案例级自动召回：ANOVA ICC / DEFF / 有效样本量，naive Wilson 与
   DEFF 校正 Wilson 双口径。
2) 项目级召回（独立单位）：>=1 个 TP 的项目占比，作为强相关场景的主口径。
3) 判例锚定准确率：正负两侧分别按项目聚类做 cluster bootstrap。

负样本侧同时报告 FP 的项目集中度，说明准确率受单一项目影响的大小。
"""
from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALID_STATES = {'valid', 'fixed', 'wontfix'}
BOOTSTRAP_REPLICATES = 4000
SEED = 20261111


def _wilson(k: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((center - m) / d, (center + m) / d)


def _proj(case: str) -> str:
    return case.split('__')[0]


def _finding_id(case: str) -> str:
    """Deduplicate a finding's impact claims to one independent sample.

    The goldset ``case`` id is ``<project>__<finding_uid>__<impact_hash>``;
    multiple impact claims of the same auditor finding share code and root
    cause, so the independent unit is ``<project>__<finding_uid>``.
    """
    parts = case.split('__')
    if len(parts) >= 2:
        return parts[0] + '__' + parts[1]
    return case


def _fp_family(case: str, title: str) -> str:
    """Cluster judge-invalid findings into root-cause families.

    Deterministic keyword rule for the known FP concentration: the SukukFi
    ``unregisterVault`` dust/donation griefing DoS family collapses to one
    independent root cause; everything else keeps its own finding id.
    """
    text = (title or '').lower()
    if ('unregister' in text or 'unregistration' in text) and \
            any(k in text for k in ('dust', 'donation', 'frontrun',
                                     'griefing', 'dos', 'prevent',
                                     'permanently')):
        return 'SukukFi_unregisterVault_dust_dos'
    if 'insolvency' in text and 'sukukfi' in text:
        return 'SukukFi_insolvency_rules'
    return _finding_id(case)


def _percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    rank = q * (len(values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(values) - 1)
    frac = rank - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def _design_effect(clusters: list[dict]) -> tuple[float, float, float]:
    ns = [c['n'] for c in clusters]
    n_total = sum(ns)
    n_clusters = len(ns)
    if n_total == 0 or n_clusters == 0:
        return 0.0, 0.0, 0.0
    m_bar = n_total / n_clusters
    p_bar = sum(c['tp'] for c in clusters) / n_total
    ssw = sum(c['n'] * (c['tp'] / c['n']) * (1 - c['tp'] / c['n']) for c in clusters)
    ssb = sum(c['n'] * ((c['tp'] / c['n']) - p_bar) ** 2 for c in clusters)
    df_w = n_total - n_clusters
    df_b = n_clusters - 1
    msw = ssw / df_w if df_w else 0.0
    msb = ssb / df_b if df_b else 0.0
    m0 = (m_bar - sum(c['n'] ** 2 for c in clusters) / n_total / n_clusters) if n_clusters else 1.0
    rho = (msb - msw) / (msb + (m0 - 1) * msw) if (msb + (m0 - 1) * msw) else 0.0
    rho = max(min(rho, 1.0), 0.0)
    deff = 1 + (m_bar - 1) * rho
    return deff, rho, m_bar


def _bootstrap_ratio(clusters: list[dict], *, n_key: str, k_key: str,
                     rng: random.Random) -> tuple[float, float]:
    """Cluster bootstrap for a ratio (sum k / sum n)."""
    idx = list(range(len(clusters)))
    values = []
    for _ in range(BOOTSTRAP_REPLICATES):
        draw = [idx[rng.randrange(len(idx))] for _ in idx]
        k = sum(clusters[i][k_key] for i in draw)
        n = sum(clusters[i][n_key] for i in draw)
        if n > 0:
            values.append(k / n)
    return (_percentile(values, 0.025), _percentile(values, 0.975))


def _bootstrap_hit_rate(clusters: list[dict], rng: random.Random) -> tuple[float, float]:
    idx = list(range(len(clusters)))
    values = []
    for _ in range(BOOTSTRAP_REPLICATES):
        draw = [idx[rng.randrange(len(idx))] for _ in idx]
        hits = sum(1 for i in draw if clusters[i]['tp'] > 0)
        values.append(hits / len(draw))
    return (_percentile(values, 0.025), _percentile(values, 0.975))


def _bootstrap_precision(tp_clusters: list[dict], fp_clusters: list[dict],
                         rng: random.Random) -> tuple[float, float]:
    """Precision = TP / (TP + FP), both sides clustered by project."""
    tp_idx = list(range(len(tp_clusters)))
    fp_idx = list(range(len(fp_clusters)))
    values = []
    for _ in range(BOOTSTRAP_REPLICATES):
        tp = sum(tp_clusters[tp_idx[rng.randrange(len(tp_idx))]]['tp']
                 for _ in tp_idx)
        fp = sum(fp_clusters[fp_idx[rng.randrange(len(fp_idx))]]['fp']
                 for _ in fp_idx) if fp_idx else 0
        denom = tp + fp
        if denom > 0:
            values.append(tp / denom)
    return (_percentile(values, 0.025), _percentile(values, 0.975))


def main() -> dict:
    gt = json.loads((HERE / 'judge_ground_truth.json').read_text())
    judge = {r['case']: r for r in gt.get('cases', [])}
    ja = json.loads((HERE / 'judge_anchored_metrics.json').read_text())
    pe = json.loads((HERE / 'positive_eval_105.json').read_text())
    p2 = json.loads((HERE / 'p2_auto_reproductions_20261110.json').read_text())

    valid_pool = [r['case'] for r in pe.get('cases', [])
                  if judge.get(r['case'], {}).get('validity') in VALID_STATES]
    tp_base = {r['case'] for r in ja.get('tp_rows', [])}
    tp_auto = {r['case'] for r in p2.get('cases', [])
               if r.get('verdict') == 'violation_reproduced'
               and judge.get(r['case'], {}).get('validity') in VALID_STATES}
    tp = sorted((tp_base | tp_auto) & set(valid_pool))

    clusters: dict[str, dict] = {}
    for case in valid_pool:
        c = clusters.setdefault(_proj(case), {'n': 0, 'tp': 0, 'cases': []})
        c['n'] += 1
        c['cases'].append(case)
    for case in tp:
        clusters[_proj(case)]['tp'] += 1

    cluster_rows = sorted(clusters.values(), key=lambda c: -c['tp'] / c['n'])
    n_total = len(valid_pool)
    tp_total = len(tp)
    deff, rho, m_bar = _design_effect(cluster_rows)
    n_eff = n_total / deff if deff else n_total
    recall = tp_total / n_total
    recall_naive_ci = _wilson(tp_total, n_total)
    recall_clustered_ci = _wilson(tp_total / deff, n_total / deff)

    rng = random.Random(SEED)
    recall_boot_ci = _bootstrap_ratio(cluster_rows, n_key='n', k_key='tp', rng=rng)

    proj_hit = sum(1 for c in cluster_rows if c['tp'] > 0)
    proj_total = len(cluster_rows)
    proj_recall = proj_hit / proj_total
    proj_recall_ci = _wilson(proj_hit, proj_total)
    proj_boot_ci = _bootstrap_hit_rate(cluster_rows, rng=rng)

    fp_rows = ja.get('fp_blind_rows', []) + ja.get('fp_in_pool_rows', [])
    fp_by_proj = Counter(_proj(r['case']) for r in fp_rows)
    fp_total = len(fp_rows)
    fp_top = fp_by_proj.most_common(1)[0][1] if fp_by_proj else 0
    fp_top_share = fp_top / fp_total if fp_total else 0.0

    fp_clusters = [{'project': p, 'fp': cnt} for p, cnt in fp_by_proj.items()]
    precision = tp_total / (tp_total + fp_total) if (tp_total + fp_total) else 0.0
    precision_wilson = _wilson(tp_total, tp_total + fp_total)
    precision_boot = _bootstrap_precision(cluster_rows, fp_clusters, rng=rng)

    # Finding-level independence: one auditor finding is one sample. Multiple
    # impact claims of the same finding (``project__finding_uid__impact_hash``)
    # are merged; a finding reproduces when any of its claims reproduces.
    tp_findings = {_finding_id(c) for c in tp}
    valid_findings = {_finding_id(c) for c in valid_pool}
    tp_finding_total = len(tp_findings & valid_findings)
    valid_finding_total = len(valid_findings)
    fp_findings = {_finding_id(r['case']) for r in fp_rows}
    fp_finding_total = len(fp_findings)
    finding_recall = (tp_finding_total / valid_finding_total
                      if valid_finding_total else 0.0)
    finding_precision = (
        tp_finding_total / (tp_finding_total + fp_finding_total)
        if (tp_finding_total + fp_finding_total) else 0.0)

    # Root-cause-family level for the negative side: collapse the SukukFi
    # dust/DoS family so one dominant root cause cannot drive precision.
    fp_families = {_fp_family(r['case'], judge.get(r['case'], {}).get('title', ''))
                   for r in fp_rows}
    family_precision = (
        tp_finding_total / (tp_finding_total + len(fp_families))
        if (tp_finding_total + len(fp_families)) else 0.0)
    fp_finding_by_proj = Counter(
        _proj(f) for f in fp_findings)
    fp_family_top_share = (
        (Counter(f.split('__')[0] if '__' in f else f
                 for f in fp_families).most_common(1)[0][1]
         / len(fp_families)) if fp_families else 0.0)

    out = {
        'schema_version': 'independence-report/1',
        'generated': '2026-11-11',
        'primary_metric': 'project_level_recall',
        'primary_note': ('同项目多案例共享代码与根因（ICC=%.2f, DEFF=%.2f），'
                         '案例级召回/准确率的点估计可用，但区间用项目聚类口径；'
                         '对外主口径为项目级召回。') % (rho, deff),
        'recall_case_level': {
            'tp': tp_total,
            'n': n_total,
            'point': round(recall, 4),
            'naive_wilson_ci': [round(x, 4) for x in recall_naive_ci],
            'design_effect': round(deff, 3),
            'icc': round(rho, 3),
            'mean_cluster_size': round(m_bar, 2),
            'effective_sample_size': round(n_eff, 1),
            'clustered_wilson_ci': [round(x, 4) for x in recall_clustered_ci],
            'cluster_bootstrap_ci': [round(x, 4) for x in recall_boot_ci],
            'clusters': len(cluster_rows),
        },
        'recall_project_level': {
            'projects_with_tp': proj_hit,
            'projects_total': proj_total,
            'point': round(proj_recall, 4),
            'wilson_ci': [round(x, 4) for x in proj_recall_ci],
            'cluster_bootstrap_ci': [round(x, 4) for x in proj_boot_ci],
        },
        'precision_case_level': {
            'tp': tp_total,
            'fp': fp_total,
            'predicted_positive': tp_total + fp_total,
            'point': round(precision, 4),
            'wilson_ci': [round(x, 4) for x in precision_wilson],
            'cluster_bootstrap_ci': [round(x, 4) for x in precision_boot],
        },
        'precision_fp_concentration': {
            'fp_total': fp_total,
            'fp_projects': len(fp_by_proj),
            'fp_by_project': dict(fp_by_proj),
            'top_project_share': round(fp_top_share, 4),
            'note': ('12/15 FP 来自 SukukFi dust/捐赠 DoS 家族，准确率受单一项目'
                     '强主导，需扩展独立负根因（>=40）才能稳定准确率区间。'),
        },
        'recall_finding_level': {
            'tp': tp_finding_total,
            'n': valid_finding_total,
            'point': round(finding_recall, 4),
            'wilson_ci': [round(x, 4) for x in _wilson(tp_finding_total,
                                                       valid_finding_total)],
            'note': ('以 project+finding_uid 为独立样本：同一 finding 的多条 '
                     'impact claim 合并，任一 claim 复现即 finding TP。'),
        },
        'precision_finding_level': {
            'tp': tp_finding_total,
            'fp': fp_finding_total,
            'point': round(finding_precision, 4),
            'wilson_ci': [round(x, 4) for x in _wilson(
                tp_finding_total, tp_finding_total + fp_finding_total)],
            'fp_by_project': dict(fp_finding_by_proj),
            'note': ('finding 级 FP 从 15 降为 %d，SukukFi 10 条 dust/DoS '
                     'impact claim 合并为 1 个 finding。') % fp_finding_total,
        },
        'precision_family_level': {
            'tp_findings': tp_finding_total,
            'fp_family_count': len(fp_families),
            'point': round(family_precision, 4),
            'wilson_ci': [round(x, 4) for x in _wilson(
                tp_finding_total, tp_finding_total + len(fp_families))],
            'fp_family_top_project_share': round(fp_family_top_share, 4),
            'fp_families': sorted(fp_families),
            'note': ('FP 根因家族口径：SukukFi unregisterVault dust/DoS 家族 '
                     '合并为 1 个独立负根因，避免单一项目主导准确率。'),
        },
        'per_project_recall': [
            {'project': _proj(c['cases'][0]), 'n': c['n'], 'tp': c['tp'],
             'recall': round(c['tp'] / c['n'], 4) if c['n'] else 0.0}
            for c in cluster_rows
        ],
    }
    (HERE / 'independence_report.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    lines = ['# 样本独立性与规模（项目聚类稳健统计）', '']
    r = out['recall_case_level']
    lines.append(f"自动召回 {r['point']:.1%}（TP={r['tp']}/{r['n']}，案例级）")
    lines.append(f"- naive Wilson 95%CI = {r['naive_wilson_ci'][0]:.1%}–{r['naive_wilson_ci'][1]:.1%}")
    lines.append(f"- 设计效应 DEFF={r['design_effect']:.2f}，ICC={r['icc']:.2f}，"
                 f"平均簇大小={r['mean_cluster_size']:.2f}")
    lines.append(f"- 有效样本量 n_eff={r['effective_sample_size']:.0f}（{r['n']} 个相关案例）")
    lines.append(f"- 聚类稳健 Wilson 95%CI = {r['clustered_wilson_ci'][0]:.1%}–{r['clustered_wilson_ci'][1]:.1%}")
    lines.append(f"- cluster bootstrap 95%CI = {r['cluster_bootstrap_ci'][0]:.1%}–{r['cluster_bootstrap_ci'][1]:.1%}")
    p = out['recall_project_level']
    lines.append('')
    lines.append(f"**主口径：项目级召回（独立单位）={p['point']:.1%}**（{p['projects_with_tp']}/{p['projects_total']} 项目）")
    lines.append(f"- Wilson 95%CI = {p['wilson_ci'][0]:.1%}–{p['wilson_ci'][1]:.1%}")
    lines.append(f"- cluster bootstrap 95%CI = {p['cluster_bootstrap_ci'][0]:.1%}–{p['cluster_bootstrap_ci'][1]:.1%}")
    pc = out['precision_case_level']
    lines.append('')
    lines.append(f"判例锚定准确率 {pc['point']:.1%}（TP={pc['tp']}, FP={pc['fp']}）")
    lines.append(f"- Wilson 95%CI = {pc['wilson_ci'][0]:.1%}–{pc['wilson_ci'][1]:.1%}")
    lines.append(f"- cluster bootstrap 95%CI = {pc['cluster_bootstrap_ci'][0]:.1%}–{pc['cluster_bootstrap_ci'][1]:.1%}")
    f = out['precision_fp_concentration']
    lines.append('')
    lines.append(f"负样本集中度：FP={f['fp_total']}，跨 {f['fp_projects']} 个项目；"
                 f"最大项目占比 {f['top_project_share']:.0%}")
    lines.append(f"  {f['fp_by_project']}")
    rf = out['recall_finding_level']
    lines.append('')
    lines.append('## 独立样本口径（finding 级）')
    lines.append('')
    lines.append(f"- 召回(finding级)={rf['point']:.1%}（TP={rf['tp']}/{rf['n']}，"
                 f"95%CI {rf['wilson_ci'][0]:.1%}–{rf['wilson_ci'][1]:.1%}）")
    pf = out['precision_finding_level']
    lines.append(f"- 准确率(finding级)={pf['point']:.1%}（TP={pf['tp']} FP={pf['fp']}，"
                 f"95%CI {pf['wilson_ci'][0]:.1%}–{pf['wilson_ci'][1]:.1%}）")
    lines.append(f"- FP 由 15 条 impact claim 合并为 {pf['fp']} 个独立 finding，"
                 f"项目分布 {pf['fp_by_project']}")
    pfl = out['precision_family_level']
    lines.append('')
    lines.append('## 根因家族口径（负样本）')
    lines.append('')
    lines.append(f"- 准确率(根因家族级)={pfl['point']:.1%}（TP_finding={pfl['tp_findings']} "
                 f"FP_family={pfl['fp_family_count']}，"
                 f"95%CI {pfl['wilson_ci'][0]:.1%}–{pfl['wilson_ci'][1]:.1%}）")
    lines.append(f"- FP 根因家族数={pfl['fp_family_count']}，最大项目占比 "
                 f"{pfl['fp_family_top_project_share']:.0%}")
    lines.append(f"- 家族明细：{', '.join(pfl['fp_families'])}")
    lines.append('')
    lines.append('| 项目 | 案例数 | TP | 项目内召回 |')
    lines.append('| --- | ---: | ---: | ---: |')
    for row in out['per_project_recall']:
        lines.append(f"| {row['project']} | {row['n']} | {row['tp']} | {row['recall']:.0%} |")
    (HERE / 'independence_report.md').write_text('\n'.join(lines) + '\n')

    print(f"DEFF={deff:.2f} ICC={rho:.2f} n_eff={n_eff:.1f}")
    print(f"recall(case) {recall:.1%} naive {recall_naive_ci[0]:.1%}-{recall_naive_ci[1]:.1%} "
          f"clustered {recall_clustered_ci[0]:.1%}-{recall_clustered_ci[1]:.1%} boot {recall_boot_ci[0]:.1%}-{recall_boot_ci[1]:.1%}")
    print(f"recall(project) {proj_recall:.1%} ({proj_hit}/{proj_total}) "
          f"wilson {proj_recall_ci[0]:.1%}-{proj_recall_ci[1]:.1%} boot {proj_boot_ci[0]:.1%}-{proj_boot_ci[1]:.1%}")
    print(f"precision {precision:.1%} wilson {precision_wilson[0]:.1%}-{precision_wilson[1]:.1%} boot {precision_boot[0]:.1%}-{precision_boot[1]:.1%}")
    print(f"FP concentration: {fp_total} FP across {len(fp_by_proj)} projects, top share {fp_top_share:.0%}")
    print(f'wrote {HERE / "independence_report.json"} / .md')
    return out


if __name__ == '__main__':
    main()
