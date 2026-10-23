# semantic-live-23 Impact qualifier blind test

## Results

Ten unseen reports were frozen before model calls. This run used the `/6` plan contract with class-specific pattern fields, Impact qualifier context, the eight-item inventory limit, and structural validation before relation alignment.

| Measure | Result |
| --- | ---: |
| Reports | 10 |
| Impact items | 31 |
| Complete P/I/V items | 3/31 |
| Reports with every selected impact formalized | 1/10 |
| Candidate checks passed | 3/10 |
| Zero-call offline replay | 10/10 |
| Blind P/I/V review | 2 faithful, 1 weakened |

The three reports passing candidate checks were GTE Perps (1/3 impacts formalized), Hybra (1/2), and Monetrix (1/1). The three generated claims received a report-only, two-phase review using the same model family as generation: GTE Perps and Monetrix were rated faithful; Hybra was rated weakened. This is not an independent human gold score.

The earlier live21 `KeyError` failures and live22 bulk relation-template mismatch did not recur in this run. The corrected prompt now states each compiler-fixed pattern and its required fields; the synthesizer validates a pattern before source alignment. The remaining main rejection families are impact-context symbol grounding, P/I/V relationship feasibility, and P-symbol source grounding. End-to-end output improved for this new sample, but 28/31 impacts remain unformalized and the sample cannot be compared directly with live22.

## Limits

Verbatim source validation proves accepted impact text occurs in the explicitly marked fragments; it does not prove every harm was extracted. The reviewer shares the generation model family. Candidate checks and solver consistency are not independent fidelity judgments.

## Artifacts

- `SELECTION.json` and manifests: frozen cases and hashes.
- `runs/`: complete prompt, response, plan, validation, and status records.
- `FAITHFULNESS_CANDIDATES.json`: independent report-only summaries and claim ratings.
- `OFFLINE_REPLAY.json`: all ten cases replayed with zero model calls.
