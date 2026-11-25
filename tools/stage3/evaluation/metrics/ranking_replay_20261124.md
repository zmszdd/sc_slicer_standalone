# Stage-3 Claim Ranking Offline Replay

- Protocol: `mainline/1.7.33`
- Read-only: `true`
- Sample: 54 non-zero-claim cases, 211 claims (33 positive / 21 negative)
- Known current-protocol outcomes: 129 / 211; unknown claims are never counted as success.

The paper-style variant is a deterministic proxy, not a reproduction: this project has no human reference-property corpus and the proxy uses report impact text instead.

## Top-3 Comparison

| variant | selected | known | completion(known) | binding(known) | eligible(known) | reproduced | known capture | cases captured | snapshot risk | duplicate-impact cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current` | 130 | 129 | 0.9923 | 0.8915 | 0.1938 | 8 | 1.0000 | 5/5 | 81 | 21 |
| `observability` | 130 | 124 | 0.9538 | 0.8952 | 0.1935 | 8 | 1.0000 | 5/5 | 79 | 20 |
| `observability_diverse` | 130 | 120 | 0.9231 | 0.9000 | 0.2000 | 8 | 1.0000 | 5/5 | 79 | 15 |
| `paper_proxy` | 130 | 99 | 0.7615 | 0.8990 | 0.1919 | 6 | 0.7500 | 4/5 | 84 | 25 |

`completion(known)` is coverage of claims that already have a current Stage-3 result, not a success rate. `known capture` is reproduced claims selected divided by all known reproduced claims in the frozen population.

## Top-K Curve

| variant | k | selected | known | reproduced | known capture | snapshot risk | duplicate-impact cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current` | 1 | 54 | 54 | 2 | 0.2500 | 32 | 0 |
| `current` | 2 | 100 | 100 | 6 | 0.7500 | 62 | 14 |
| `current` | 3 | 130 | 129 | 8 | 1.0000 | 81 | 21 |
| `current` | 5 | 164 | 129 | 8 | 1.0000 | 105 | 24 |
| `observability` | 1 | 54 | 53 | 2 | 0.2500 | 27 | 0 |
| `observability` | 2 | 100 | 97 | 6 | 0.7500 | 60 | 12 |
| `observability` | 3 | 130 | 124 | 8 | 1.0000 | 79 | 20 |
| `observability` | 5 | 164 | 127 | 8 | 1.0000 | 102 | 24 |
| `observability_diverse` | 1 | 54 | 53 | 2 | 0.2500 | 27 | 0 |
| `observability_diverse` | 2 | 100 | 98 | 6 | 0.7500 | 61 | 9 |
| `observability_diverse` | 3 | 130 | 120 | 8 | 1.0000 | 79 | 15 |
| `observability_diverse` | 5 | 164 | 125 | 8 | 1.0000 | 102 | 21 |
| `paper_proxy` | 1 | 54 | 46 | 3 | 0.3750 | 32 | 0 |
| `paper_proxy` | 2 | 100 | 80 | 5 | 0.6250 | 65 | 23 |
| `paper_proxy` | 3 | 130 | 99 | 6 | 0.7500 | 84 | 25 |
| `paper_proxy` | 5 | 164 | 114 | 8 | 1.0000 | 105 | 27 |

## Findings

- Current Top-3 selects 130 claims; 81 carry snapshot/transition risk and 21 cases contain repeated impact variants.
- Observability-first with impact diversity overlaps the current selection on 121 claims; known reproduced delta is 0, snapshot-risk delta is -2, duplicate-impact-case delta is -6.
- The replay cannot establish a metric lift because most newly selected claims have no current-protocol execution result. Any claim of recall improvement requires a protocol bump and a full rerun.
- All 211 claims carry `I_MUTATION_SITE_MISSING` and `OBSERVABILITY_REQUIRES_CODE_FACT`. This is a Stage-2 observability defect, not a ranking-weight defect; no ranker can manufacture a missing mutation site or code fact.

## Recommendation

1. Do not replace the authoritative Top-3 ranking from this replay alone.
2. Fix the upstream mutation-site/observable evidence gap first; the ranker can only choose among equally unobservable claims today.
3. If a protocol bump is approved, use observability-first plus one claim per impact as the candidate ranking, then rerun and compare coverage-aware metrics against this baseline.

