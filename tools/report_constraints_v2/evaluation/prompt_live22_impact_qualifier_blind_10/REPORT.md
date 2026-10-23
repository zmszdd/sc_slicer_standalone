# semantic-live-22 Impact qualifier blind test

## Results

Ten unseen reports were frozen before model calls. The run used the eight-item Impact limit, formal-plan `/6`, qualifier context checks, and the class-template instructions as they stood at the time of this run.

| Measure | Result |
| --- | ---: |
| Reports | 10 |
| Reports with an explicitly marked Impact area | 8 |
| No marked Impact section | 2 |
| Impact items extracted | 33 |
| Complete P/I/V items | 5/33 |
| Reports with all selected impacts formalized | 1/10 |
| Candidate checks passed | 3/10 |
| Zero-call offline replay | 10/10 |

The 5 completed items came from three reports: Kinetiq completed 2/2, GTE Spot completed 2/7, and Monetrix completed 1/2. Larger lists passed the expanded path, including a six-item Covenant inventory and a seven-item GTE Spot inventory. Two reports without a marked Impact section stopped at impact review.

The three candidate-check reports received a two-phase report-only P/I/V review using the same model family as generation. Kinetiq was rated faithful; GTE Spot and Monetrix were rated weakened. The GTE Spot review found the safety intent broadened beyond the report's attack-specific fee impact. The Monetrix review found an extra precondition and a weakened unconditional safety intent. This is diagnostic evidence, not an independent human gold score.

This run removed the bulk template mismatch and KeyError behavior seen in earlier development runs, and produced five complete P/I/V items. It still left 28/33 impacts unformalized; blind review found two of the three candidate reports weakened. The remaining P/I/V issue is therefore material. The run's prompt also contained stale state-correspondence and per-kind field instructions, corrected after the run; see the final follow-up experiment when available.

## Limits

The 10 reports are a new cohort, so their counts are not directly comparable with live16. Verbatim source validation proves every accepted inventory string is present in an allowed Impact fragment, not that every harm was found. The reviewer shares the generator's model family. Candidate checks are not a substitute for that review.

## Artifacts

- `SELECTION.json`, manifests: frozen sample, exclusions and hashes.
- `runs/`: prompts, responses, inventories, plans, status and validation records.
- `FAITHFULNESS_CANDIDATES.json`: report-only reference summaries and claim ratings.
- `OFFLINE_REPLAY.json`: all ten bundles replayed with zero model calls.
