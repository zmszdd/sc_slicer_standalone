# semantic-live-22 frozen-source relation-context retest

## Method

- Reused all 52 exact `(Impact, I source, P source set)` cards from `prompt_live21_frozen_sources_paired`; 9 reports were included. No P/I/V source was reselected.
- Generated each rule with `semantic-live-22` and `deepseek-flash`. The single post-generation audit received the selected P/I/V formulas plus exact report excerpts cited by extracted action/root-cause statements. Those excerpts were used only to assess the relationship; they did not change the frozen sources or formulas.
- Role-specific formula repair remained limited to P/I/V source transcription findings. A relationship-only concern did not trigger edits to individually faithful formulas.
- The run made 115 external model calls. Six source pairs did not produce a rule.

## Results

| Outcome | Count out of 52 |
|---|---:|
| Rules generated | 46 |
| Complete P/I/V audit passed | 33 |
| Relationship needs review | 10 |
| Audit failed | 3 |
| No rule generated | 6 |
| Audit unavailable | 0 |

Among 46 generated rules, 44/46 had all P/I/V source transcriptions marked consistent. The remaining two had an I transcription mismatch. Relationship verdicts were consistent for 33, weakened for 12, and mismatch for 1. Two of the weakened cases also had an I transcription mismatch, so the final statuses are 33 passed, 10 needs review, and 3 failed.

## Comparison with live-21 on the same frozen source set

| Version | Generated | Passed | Needs review | Failed | Audit unavailable | No rule |
|---|---:|---:|---:|---:|---:|---:|
| live-21 | 46 | 21 | not separated | 24 | 1 | 6 |
| live-22 | 46 | 33 | 10 | 3 | 0 | 6 |

The live-21 audit grouped weakened relations with failures. On the same 46 generated rules, live-22 has 12 more clear passes and one fewer unavailable review; it also isolates 10 weakened relationships for review instead of treating them as definite failures. Generation coverage stayed unchanged. Since model outputs are sampled, the frozen sources control source-selection variation but do not make this a deterministic model comparison.

## Targeted cases

- **Panoptic Hypovault:** 7/12 rules generated; 6 passed, 1 failed, and 5 did not generate. For the passing cases, the action/root-cause excerpts explicitly connected the bootstrap supply/zero-asset scenario to the reported share or loss outcome. The failed case had a tautological I formula, so it was correctly classified as a formula-mapping failure even though the relation itself was only weakened.
- **Monetrix:** all 8 rules generated, and all 8 need review. The excerpts connect unreadable or stale accounting slots to reverting reads and blocked settlement, but the audit still could not establish the specific bridge between the selected pending/registration intent and each selected impact. This is a limitation in the report-grounded relationship evidence, not a reason to rewrite individually faithful P/I/V formulas.

## Conclusion

The change improves the audit's ability to recognize report-described indirect links without adding another review call or weakening the requirement that only `passed` pairs enter stage three. It substantially reduced definite audit failures in this frozen-source run. The remaining main issue is relationship evidence for Monetrix, alongside two I formula mismatches and six rule-generation failures. Keep `needs_review` separate from `passed`; do not count it as stage-three eligible until the report text supports the link or the formulas faithfully express it.
