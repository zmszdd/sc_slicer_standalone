# semantic-live-15 影响项粒度与语气盲测

## 设计

模型调用前冻结 5 份未见报告。提取只读取明确标注的 Impact 区域；校验器只忽略列表编号、Markdown 粗体/代码展示符号和空白，影响正文仍须逐字匹配来源。提示词规定一项对应一个独立明示后果，避免重复或重叠片段；形式化提示词要求 potential 影响保持条件/可能性，无法忠实表达时阻塞而不写成必然结果。

## 结果

| 指标 | 结果 |
| --- | ---: |
| 冻结报告 | 5 |
| 提取与形式化模型调用 | 35 |
| 候选检查通过 | 4/5 |
| 已提取影响项 | 8 |
| 完整 P/I/V | 5/8 (62.5%) |
| 无明确标注区域 | 1/5 |
| 逐报告零调用重放 | 5/5 |
| 候选 P/I/V 审查 | 3 faithful, 1 weakened |
| 要素级审查 | 14 pass, 1 partial |

此前被拒的 Merkl 原始输出经新校验器复验通过：校验忽略列表序号、粗体和行内代码标记，正文词句保持原样。新盲测中没有因这类 Markdown 展示差异拒绝的报告。5/5 份均零调用重放成功。

本轮 5 份报告里，4 份候选通过；8 个明示影响项中 5 个完成 P/I/V。只有一个 `potential` 项，盲审评为 faithful，说明该例保留了可能性限定；样本太小，不能据此推断总体语气保真率。盲审模型与生成模型同属一个模型族，只作诊断。

## 逐报告结果

| Case | 状态 | 影响数 | 完整 P/I/V | 模态 | 清单歧义 |
| --- | --- | ---: | ---: | --- | ---: |
| `Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__5pt4vrEZuyz` | candidate_checks_passed | 2 | 2/2 | asserted, asserted | 1 |
| `Covenant_d4uY8y2AMSs__Jk2Mbvck9TA__KY7fciERz5c` | needs_impact_review | 0 | 0/0 | — | 1 |
| `Ekubo_3FTodhsvBkM__dtK3s8JSnTx__JjiXEStHW6S` | candidate_checks_passed | 1 | 1/1 | potential | 0 |
| `Forte__Float128_Solidity_Library_evjHaYmvKxh__XC3hjxc6iXk__byxbibYSNcy` | candidate_checks_passed | 1 | 1/1 | asserted | 1 |
| `GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__SyZM6dWoy4F` | candidate_checks_passed | 4 | 1/4 | asserted, asserted, asserted, asserted | 1 |

## 判断

展示格式误拒问题已针对性修复，且旧拒绝样例通过新的确定性验证；Impact 区域边界继续保持。影响项是否拆得不重不漏、P/I/V 是否完整仍未被充分证明，5 份样本不足以衡量覆盖率。下一步应对本轮有多条影响的报告做人工原文逐项核对，并继续跟踪被标记为 `needs_review` 的清单；不能把候选通过当作完整性证明。

## 产物

- `SELECTION.json` 与 `manifest_01.json`：冻结样本。
- `runs/`：输入、模型调用、清单、P/I/V 与状态。
- `OFFLINE_REPLAY.json`：零调用离线重放。
- `FAITHFULNESS_CANDIDATES.json`：P/I/V 忠实度诊断。
