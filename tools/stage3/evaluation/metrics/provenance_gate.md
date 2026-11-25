# Provenance / metric refresh gate

| item | value |
| --- | --- |
| mode | `mainline-only/1` |
| fingerprinted claims | 0 |
| legacy or missing | 0 |
| current only | False |
| refresh allowed | True |

## Current denominator

| dataset | eligible | excluded/retry | unresolved |
| --- | ---: | ---: | ---: |
| dev252 | 0 | 0 | 0 |
| dev24 | 0 | 24 | 0 |
| negative5 | 0 | 0 | 0 |

## Blocking reasons

- none

## dev24 gate

| gate | value |
| --- | --- |
| `negative_fp_zero` | True |
| `negative_consistency_fp_zero` | False |
| `negative_all_resolved` | False |
| `positive_tp_not_below_baseline` | True |
| `all_runs_done` | True |
