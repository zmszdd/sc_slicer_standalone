# Stage 2 blind evaluation: 50 reports

## Objective and setup

This run measures whether the current Stage 2 pipeline can extract and formalize report-grounded P/I/V rules. Faithfulness is reported as a secondary check. Stage 3 repair generation and ablation experiments were not performed.

The frozen sample contains 50 distinct, previously unseen reports from 18 projects. Selection was round-robin by project, and reports were frozen before generation. The run used `semantic-live`, DeepSeek Flash, one element retry and one formalization retry. See `SELECTION.json` and the per-batch manifests for hashes and run settings.

## Results

| Measure | Result |
| --- | ---: |
| Reports run | 50 |
| Input readiness: ready | 49/50 (98%) |
| Input readiness: insufficient | 1/50 (2%) |
| Complete P/I/V candidate checks passed | 17/50 (34%) |
| Ready reports that passed candidate checks | 17/49 (35%) |
| Reports needing formalization review | 32/50 (64%) |
| Formalized impact claims | 70/134 (52%) |
| Impact claims with no P, I, or V formula | 64/134 (48%) |

The per-claim result was all-or-none in these artifacts: 70 claims had expressions for P, I, and V; 64 claims had no expression for any of the three roles. This is a useful target for the next improvement cycle.

The only report rejected at input screening lacked a concrete direct effect and a clear safety-relation basis. In contrast, 32 reports were judged ready but did not produce a complete formalization. That gap indicates that the main bottleneck in this sample is formalization after screening, rather than the input screen alone.

## Candidate faithfulness review

The 17 reports that passed candidate checks were given a separate P/I/V-only review:

| Review outcome | Reports |
| --- | ---: |
| Faithful | 10/17 (59%) |
| Weakened | 7/17 (41%) |
| Unfaithful | 0/17 |

Across 41 generated claims, the reviewer rated 37 P expressions, 34 I expressions, and 32 V expressions fully supported. The remaining ratings were partial: 4 P, 7 I, and 9 V. The recurring weaknesses were omitted triggers or causal steps, missing material conditions, and safety intent broadened beyond the report. This review uses DeepSeek Flash, the same model family as generation, and is not an independent human gold standard.

Faithfulness was not used to redefine the 17/50 candidate-generation rate. A candidate can pass structural checks and still weaken a report detail.

## Failure patterns

The 32 needs-review reports contain repeated errors across formalization attempts. The most frequent recorded error was `local repair made no change` (21 occurrences). Other recurring errors included invalid quantity bindings (9), numeric P bounds hidden by non-comparison predicates (8), and missing grounding for core relation observables (5). There were also repeated P-source grounding, unit/type, and relation-direction failures. Error occurrences can repeat within a report and are not independent case counts.

These patterns point to three Stage 2 improvement targets:

1. Make repair attempts change the failing predicate or relation, and avoid spending a retry on a structurally unchanged plan.
2. Improve construction and validation of numeric P predicates, quantity expressions, units, and source bindings.
3. Preserve the report's concrete triggers, causal chain, and safety intent when completing I/V and the direct P/I/V relation.

## Offline replay

The read-only verifier replayed 47 of the 49 reports that produced formalization artifacts. One additional report stopped at input screening and correctly has no `elements.json`. Two Ekubo artifacts failed exact SMT replay with `SMT replay mismatch`. The local verifier environment used Z3 5.3.1; the saved runs do not pin the solver version, so these two mismatches are unresolved reproducibility issues and are not counted as confirmed semantic errors.

## Conclusion and next step

The P/I/V completeness problem is real in this blind sample: despite 49/50 reports passing input readiness, only 17/49 ready reports yielded complete candidates, and 64 impact claims had no P/I/V formulas. The current pipeline is not ready for unattended field use.

The next Stage 2 cycle should target the three repeated failure patterns above, then rerun the same frozen reports as a regression comparison and add a separate human review of a stratified sample of generated and missing claims. Do not infer repair effectiveness, ablation results, or superiority to commercial methods from this evaluation.
