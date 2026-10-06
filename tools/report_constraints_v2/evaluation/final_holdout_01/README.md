# final_holdout_01 — 终局保留批（反过拟合仪器）

冻结于 2026-10-06，在 live-3 迭代开始**之前**。零模型调用，纯选样冻结
（`select.py`，盐 `stage2-final-holdout-2026-10-06-01:`，排除全部 102 个历史
case ID / 104 个报告哈希 / 108 个输入哈希）。

## 规则（写入 `docs/PROMPT_LIVE_POLICY.md`，此处为执行说明）

- **本批永不进迭代**：任何 live-3/live-4 迭代批的 select.py 都会扫描
  `evaluation/**/SELECTION.json` 自动排除这 10 例（case ID + 报告哈希 + 输入
  哈希三重排除）。
- **迭代期间无人看它**：不对这些案例做任何语义检查、probe 或离线试跑。
- **循环停止后只跑一次**：用当时的 `semantic-live` prompt（终端 run 自己落
  prompt 快照，本文件不钉 prompt 哈希）跑 `manifest_a.json` + `manifest_b.json`
  两批（batch runner 单 manifest 上限 5 例），合成 n=10。这是整个迭代循环
  产出的唯一无偏数字。
- **报告必须披露迭代轮数**：终局报告注明"经 N 轮自适应迭代后测得"。

## 停止规则（2026-10-06 与用户约定）

最多再迭代 2 轮（live-3、live-4）；任一轮相对上一盲批无实测改善即提前停。
