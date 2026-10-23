# semantic-live-23 frozen-source relation-context generation retest

## Method

- Reused the exact 52 `(Impact, I source, P source set)` pairs from `prompt_live21_frozen_sources_paired`; source IDs were not reselected.
- Compared against the preceding live-22 run on those same pairs. The model (`deepseek-flash`) and post-generation audit remained the same.
- Added the report excerpts cited by already extracted action/root-cause statements to the rule-generation input as `relation_context`, as well as the audit input. The prompt restricts that context to explaining a report-described bridge; it cannot add P/I/V sources or alter their roles.
- Added a specific prompt check against tautological/vacuous I patterns and asked the audit to cite the statement/evidence IDs supporting its relationship verdict.
- The run made 122 model calls. Six of the 52 source pairs produced no rule.

## Results

| Outcome | live-22 | live-23 |
|---|---:|---:|
| Frozen source pairs | 52 | 52 |
| Rules generated | 46 | 46 |
| Passed | 33 | 36 |
| Needs review | 10 | 9 |
| Failed | 3 | 1 |
| No rule generated | 6 | 6 |
| Audit unavailable | 0 | 0 |
| Model calls | 115 | 122 |

Among the generated rules, the pass rate rose from 33/46 (71.7%) to 36/46 (78.3%). The overall pass rate rose from 33/52 (63.5%) to 36/52 (69.2%). The live-23 relation verdicts were consistent 36, weakened 9, and mismatch 1. The remaining failed case had individually consistent source checks but the report evidence explicitly contradicted the selected intent relationship; it remains correctly blocked.

Paired end-state transitions live-22 → live-23 were: 30 pass→pass, 8 needs-review→needs-review, 4 no-rule→no-rule, 2 no-rule→pass, 2 fail→pass, 2 pass→no-rule, 2 needs-review→pass, 1 pass→needs-review, and 1 fail→fail. This is a sampled model comparison, so it indicates direction but does not isolate prompt effects from model sampling.

## Targeted cases

- **Panoptic Hypovault:** the same 7 of 12 pairs generated rules in both runs. Live-22 had 6 passed and 1 failed; live-23 had 7 passed. The former tautological-I case passed after the explicit vacuity guidance. Five pairs still did not generate rules.
- **Monetrix:** all 8 pairs generated in both runs. Live-22 had 8 needs-review; live-23 had 2 pass and 6 needs-review. The generation-side excerpts helped the model represent and the auditor assess some explicit registration-to-accounting links, but most selected pairs still lack a clear bridge in the available report evidence.

## Reading the result

The change moved the result in the intended direction without changing source coverage or adding a second semantic review stage: three more pairs passed, two fewer failed, and one fewer remained in needs-review. The main unresolved issue is still explicit relationship support for some report cases, especially Monetrix; six pairs also remain generation failures. Keep needs-review, failed, and no-rule outcomes out of stage three.

The audit is model-based and was not compared with an independent human gold set. These figures measure this pipeline's internal audit outcomes, not externally established semantic accuracy. Further work should target the remaining no-rule failure families and model stability on the same frozen pairs, without relaxing the pass standard.
