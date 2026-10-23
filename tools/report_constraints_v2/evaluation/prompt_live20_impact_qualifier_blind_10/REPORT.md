# semantic-live-20 impact qualifier blind test

## Scope

Ten unseen reports were frozen before model calls. The run used the updated eight-impact limit, explicit qualifier-context field in formal plan `/6`, strict Impact-area evidence validation, and zero-call replay checks.

## Results

| Measure | Result |
| --- | ---: |
| Reports | 10 |
| Explicit Impact inventories accepted | 8 |
| No marked Impact section | 1 |
| Impact inventory rejected before extraction | 1 |
| Extracted impact items | 36 |
| Reports with 5 or more extracted items | 5 |
| Complete P/I/V claims | 0/36 |
| Offline replay | 9/9 replayable cases; 0 model calls |

The 36 items were source-checked as verbatim excerpts from the marked Impact fragments. One report had no explicitly marked Impact section, so extraction stopped as designed. One model output paraphrased its cited Impact text and was rejected by the verbatim validator. The 8 accepted inventories comprise 3 `extracted` and 5 `needs_review` statuses; the latter must not be read as a completeness pass.

The expanded limit is exercised: GTE Spot and Monetrix each produced 8 inventory items, and the Hybra report produced 5. A manual comparison of the Hybra Impact bullets confirmed that all five listed outcomes appear in the accepted inventory. This is a spot check, not an exhaustive completeness score for all 10 reports.

No claim completed formalization in this batch. The live prompt contradicted the compiler about the required template for several relation classes (for example, it prescribed `relation_obligation` where the compiler requires `required_effect`). That mismatch caused many candidate rejections. Other plans failed P/I/V faithfulness checks; qualifier coverage also rejected plans that omitted detected conditions or directions. The prompt was corrected after the batch, so live20 remains development evidence and does not measure the corrected template instructions.

## Interpretation limits

This is a new sample, so item counts are not directly comparable to live16. The impact inventory checks prove that accepted text is present in the allowed fragments; they do not prove the model found every distinct harm. The one manual completeness check is limited to Hybra. Since no claim was fully formalized, P/I/V faithfulness is not evaluable here.

## Artifacts

- `SELECTION.json` and `manifest_01.json` / `manifest_02.json`: frozen sample and hashes.
- `runs/`: model prompts/responses, candidate plans, validation errors, and statuses.
- `OFFLINE_REPLAY.json`: replay result for all completed artifact bundles.
- `runs/batch-summary.json`: records the updated eight-impact budget.
