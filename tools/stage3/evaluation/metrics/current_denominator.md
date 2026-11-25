# 当前分母审计（2026-11-18）

四指标仍使用各自标准分母，但分子/样本必须来自同一个 `eligible_current` 集合。

| 数据集 | cases | eligible_current | excluded_retry | unresolved |
| --- | ---: | ---: | ---: | ---: |
| dev252 | 0 | 0 | 0 | 0 |
| dev24 | 24 | 0 | 24 | 0 |
| negative5 | 0 | 0 | 0 | 0 |
| mainline | - | 35+11 | 0 | - |

`refresh_ready`: **True**

## 排除原因

| 数据集 | bucket | reason | next_action | claims |
| --- | --- | --- | --- | ---: |
| dev24 | excluded_retry | `stale_mainline_protocol` | `rerun_with_current_mainline_protocol` | 95 |
