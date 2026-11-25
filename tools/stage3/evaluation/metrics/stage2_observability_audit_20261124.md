# Stage-2 Observability Root-Cause Audit

- Schema: `stage2-observability-audit/1`
- Read-only: `true`
- Sample: 54 cases, 211 claims, 1027 claim-level symbols (33 positive / 21 negative cases).

## Executive Summary

| Signal | Value |
| --- | ---: |
| symbols with observable_kind | 1027 |
| symbols with code_fact | 0 |
| symbols with mutation_site | 0 |
| symbols with no code evidence | 1027 |
| derived symbols missing definition | 339 |
| auto_assert claims | 58 |
| auto_assert claims without code evidence | 58 |
| status=needs_review while route=auto_assert | 58 |
| binding_review claims | 153 |
| high-risk symbols | 273 |
| observability_review claims | 263 |
| observability_established=false | 263 |

## P/I/V Coverage

| Role | Occurrences | Without code evidence | High risk | Derived missing definition |
| --- | ---: | ---: | ---: | ---: |
| P | 509 | 509 | 49 | 110 |
| I | 555 | 555 | 118 | 166 |
| V | 796 | 796 | 258 | 293 |

## Claim Routing

| Route | Claims |
| --- | ---: |
| `auto_assert` | 58 |
| `binding_review` | 153 |

## Observable Kinds

| Kind | Symbols |
| --- | ---: |
| `balance` | 30 |
| `call` | 272 |
| `derived` | 354 |
| `getter` | 28 |
| `mapping` | 20 |
| `state` | 313 |
| `struct_field` | 7 |
| `timestamp` | 3 |

## Binding Risks

| Risk | Symbols |
| --- | ---: |
| `high` | 273 |
| `low` | 189 |
| `medium` | 565 |

## Root Causes

| ID | Root cause | Severity | Evidence |
| --- | --- | --- | --- |
| OBS-1 | Stage-2/Stage-3 evidence-layer conflation | critical | 1027 symbols lack code fact/mutation site before Stage-3 |
| OBS-2 | derived kind without definition | high | 339 derived symbols missing derived_definition |
| OBS-3 | route/status inconsistency | high | 58 claims are auto_assert while status=needs_review |
| OBS-4 | no Stage-3 evidence write-back | critical | observability-review.observability_established is a constant false (263 reviewed claims); no per-symbol bound_expr/source/mutation evidence artifact is consumed by Stage-2 |
| OBS-5 | high-risk signal has no clearing rule | high | 273 high-risk symbols; A+ treats the warning as a soft quality label |

## Findings

- All 1027 claim-level symbols declare observable_kind/scope/binding_risk, but 0 declare a code_fact and 0 declare a mutation_site.
- 1027/1027 symbols have neither source_entity, code_fact nor mutation_site. This is the source of the repeated OBSERVABILITY_REQUIRES_CODE_FACT and I_MUTATION_SITE_MISSING warnings.
- 58/58 auto_assert claims therefore route to Stage-3 without any Stage-2 code evidence; the audit status says needs_review at the same time.
- 339 symbols are marked observable_kind=derived but have no derived_definition across 47 cases; 37 auto_assert claims are affected.
- 273 symbols are binding_risk=high; 153 claims are routed to binding review, showing that the risk signal exists but has no Stage-3 resolution artifact to clear it.
- 263/263 reviewed claims report observability_established=false; the review is a structural hint, not a code-binding verdict.

## Interpretation

- The Stage-2 symbols are not lacking observable *intent*: every symbol has kind, scope and binding risk.
- They are lacking code *evidence*, which Stage-2 cannot legitimately produce from report text alone.
- Treating that evidence gap as a soft warning makes the warning non-actionable; treating it as a hard rejection makes every claim unbindable. The correct fix is an explicit two-layer contract and a Stage-3 evidence write-back.
- Ranking cannot repair this gap because every candidate is equally missing the same evidence layer.

## Reproduction

```bash
cd tools/stage3
python -m evaluation.metrics.stage2_observability_audit
```

