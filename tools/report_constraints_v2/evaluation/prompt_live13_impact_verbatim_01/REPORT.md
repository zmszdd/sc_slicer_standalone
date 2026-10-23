# semantic-live-13 verbatim Impact blind evaluation

## Design

Five fresh exact-submission reports were frozen before model calls. The selector excluded prior case IDs, report hashes, and normalized input hashes and did not inspect Impact content. It used DeepSeek `deepseek-flash`, `semantic-live`, concurrency 2, one retry, and the restricted marked-Impact evidence catalog. Each new Impact statement had to be a whitespace-normalized verbatim excerpt of its cited Impact evidence; schema `/1` historical outputs were not used for generation.

## Results

| Measure | Result |
| --- | ---: |
| Frozen reports | 5 |
| Extraction/formalization calls | 58 |
| Additional P/I/V review calls | 10 |
| Candidate checks passed | 5/5 |
| Extracted Impact statements | 16 |
| Statements with complete P/I/V | 10/16 (62.5%) |
| Reports with every extracted Impact fully formalized | 1/5 |
| Reports with inventory ambiguity notes | 3/5 |
| Zero-call offline replay | 5/5 |
| Blind P/I/V review | 5/5 weakened; 23 role ratings pass, 7 partial, 0 fail |

All 16 generated Impact texts passed deterministic exact-source validation against cited fragments in explicitly marked Impact regions. The validation therefore rejected any paraphrase or out-of-region source before acceptance. The blind reviewer was the same model family as generation, so its ratings are diagnostic rather than an independent gold standard.

The five reports all received `candidate_checks_passed`, while only one had complete rule formalization across every extracted Impact. Candidate acceptance is therefore not a report-level completeness signal; check `rule_formalization_status` and `impact_completion_status` separately.

## Findings

The new constraint did what it directly targets: every accepted inventory item is traceable as exact text to the labeled Impact source, with no inferred item. It does not yet make the inventory complete or atomic. In particular, some items overlap by repeating a full sentence and a clause from that same sentence; the GTE run also records two omitted-outcome ambiguity notes.

P/I/V remains the main quality bottleneck. The report-fidelity review identified weakened formulas in all five reports, including omitted cushion/availability conditions, loss of a concrete wrong-address relation, and converting a hedged indirect effect into a definite predicate. The review is model-generated and not fully independent.

The previous live-12 blind set was different, so the apparent increase from 40.9% to 62.5% complete P/I/V is not a paired comparison and cannot establish a measured improvement.

## Case-level summary

| Case | Impacts | Complete P/I/V | Inventory | P/I/V review |
| --- | ---: | ---: | --- | --- |
| `Brix_Money_qy7NXr77sDh__cSNXN84Wruw__6uF5PJDEbv3` | 4 | 1/4 | needs_review (1 notes) | weakened |
| `Covenant_d4uY8y2AMSs__oq24Vuwjp6r__3AxUq2FDg3j` | 4 | 4/4 | extracted (0 notes) | weakened |
| `Ekubo_3FTodhsvBkM__9MpUh5dZn3f__dsuYRo9grVX` | 3 | 2/3 | extracted (0 notes) | weakened |
| `Forte__Float128_Solidity_Library_evjHaYmvKxh__hAkTyQBGSaf__z5NZSdCpmaF` | 3 | 2/3 | needs_review (1 notes) | weakened |
| `GTE_Perps_and_Launchpad_gtn2Umg6KsC__WxFog2dKdF8__yRyMuGR6QVt` | 2 | 1/2 | needs_review (2 notes) | weakened |

## Artifacts

- `SELECTION.json` and `manifest_01.json`: frozen sample and inputs.
- `runs/`: source snapshots, model calls, inventories, P/I/V outputs, and statuses.
- `OFFLINE_REPLAY.json`: zero-call replay results.
- `FAITHFULNESS_CANDIDATES.json`: role-level report-fidelity review.
