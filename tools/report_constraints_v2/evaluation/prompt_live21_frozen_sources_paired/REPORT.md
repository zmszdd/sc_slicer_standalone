# Frozen-source paired rule-generation evaluation

## Setup

- Frozen inputs: `prompt_live20_live16_paired_retest_10/runs/*/{elements-ids.json,impact-applicability.json}`.
- Included 9 reports and 52 selected `(Impact, I source, P source set)` cards; both prompt versions received the same source IDs for every pair.
- Olas was skipped because its run has no `impact-applicability.json`, so it has no source card to freeze.
- Each card was generated once with `semantic-live-19` and once with `semantic-live-20`. Both used the same current synthesis code, model (`deepseek-flash`), and post-generation P/I/V faithfulness audit. No candidate filtering or retry was enabled.
- There were 177 external model calls: 104 generation calls plus 73 audits (audit runs only after a candidate is successfully synthesized).
- The formal prompt diff confirms the material version change: live-20 requires a separately encoded `impact_outcome` (V) and uses plan schema 8; live-19 has no independent V field and uses schema 7.

## Results

| Version | Frozen cards | Rules generated | No rule | Full P/I/V audit pass | Pass / generated |
|---|---:|---:|---:|---:|---:|
| live-19 | 52 | 39 | 13 | 12 | 30.8% |
| live-20 | 52 | 34 | 18 | 5 | 14.7% |

Paired end states (live-19 → live-20): 20 fail→fail, 10 no-rule→no-rule, 7 pass→fail, 4 pass→no-rule, 4 fail→no-rule, 3 fail→pass, 2 no-rule→fail, 1 no-rule→pass, and 1 pass→pass.

Across the generated rules, per-source audit mismatch counts were:

| Role | live-19 | live-20 |
|---|---:|---:|
| P | 1 / 73 checks | 2 / 63 checks |
| I | 22 / 39 checks | 7 / 34 checks |
| V | 9 / 39 checks | 3 / 34 checks |

The separate P/I/V relation audit was consistent on 14/39 live-19 candidates and 7/34 live-20 candidates. It reported weakened/mismatch on 7/39 and 18/39 live-19 candidates, versus 14/34 and 13/34 live-20 candidates, respectively.

## Reading the result

The separate V field improved the audit's direct V-source fidelity (9 mismatches to 3) and I source-formula fidelity also improved (22 to 7). However, live-20 produced fewer usable candidates, and the strict full P/I/V pass count fell from 12 to 5. The changed V schema therefore appears to help the individual V and I mappings in this sample, but it did **not** improve end-to-end P/I/V acceptance: the relation audit still often found that the generated I and V did not establish the reported violation together.

I mapping remains a significant issue: 7/34 audited live-20 I predicates still failed source-level fidelity, including inverted time bounds, wrong consequent/ordering, and omitted pending-until-read requirements. These are concrete formula-mapping errors, not source-selection changes.

This is a one-generation-per-card comparison. Frozen IDs eliminate upstream source-selection variation, but model sampling can still vary between paired calls; the observed totals are directional evidence, not a deterministic causal estimate. The audit verdict is the measured metric and should not be read as proof of semantic correctness beyond its checks.
