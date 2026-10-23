# semantic-live-16 多报告影响项盲测

## 设计

10 份未见报告在模型调用前冻结，按 case ID、报告哈希和规范化输入哈希排除历史样本。运行使用当前语义流程：影响项只从显式标注 Impact 区域提取；确定性来源校验允许列表编号、Markdown 粗体/行内代码标记及空白差异，正文词语须逐字匹配；提示词限制重叠拆项，并要求保留 potential 条件性。

## 汇总

| 指标 | 结果 |
| --- | ---: |
| 报告 | 10 |
| 提取与形式化模型调用 | 99 |
| 候选检查通过 | 7/10 |
| 需复核 | 2/10 |
| Impact 无明确伤害结果，按规则停止 | 1/10 |
| 已提取影响项 | 28 |
| 完整 P/I/V | 14/28 (50.0%) |
| 所有已提取影响项均完成 P/I/V 的报告 | 3/10 |
| 带清单歧义说明的报告 | 4/10 |
| 零调用离线重放 | 10/10 |
| P/I/V 盲审 | 3 faithful, 4 weakened |
| 角色盲审 | 34 pass, 8 partial, 0 fail |

本轮没有逐字来源校验拒绝；10/10 重放成功。6 个影响项标为 potential，公式盲审覆盖的对应样例中仍有弱化，因此提示词要求尚不能证明一般性的语气忠实。7 份候选通过检查，但 4 份 P/I/V 盲审被评为 weakened。评审模型与生成模型同属一个模型族，不能视为独立金标准。

## 逐报告结果

| Case | 状态 | 影响数 | 完整 P/I/V | 模态 | 歧义 |
| --- | --- | ---: | ---: | --- | ---: |
| `Brix_Money_qy7NXr77sDh__Nxh87eHBt9G__qCYX2Sr7YEq` | candidate_checks_passed | 3 | 3/3 | asserted, asserted, asserted | 1 |
| `Covenant_d4uY8y2AMSs__Jk2Mbvck9TA__92rPRhqqUax` | needs_review | 4 | 0/4 | asserted, asserted, asserted, asserted | 1 |
| `Ekubo_3FTodhsvBkM__uPQxpkt7qin__5cvoTowJqyq` | needs_review | 1 | 0/1 | asserted | 0 |
| `Forte__Float128_Solidity_Library_evjHaYmvKxh__hAkTyQBGSaf__LCgWyF4yckg` | needs_impact_review | 0 | 0/0 | — | 0 |
| `GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__dsRstjv5gQ9` | candidate_checks_passed | 4 | 3/4 | asserted, asserted, asserted, asserted | 0 |
| `GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__EXx2KHrPZfx__Pmuhk6hL7Sz` | candidate_checks_passed | 3 | 1/3 | potential, potential, potential | 0 |
| `Hybra_Finance_xo4hapwL2Jy__4hPkdyb8kNg__Fh34wvW4Ctu` | candidate_checks_passed | 4 | 1/4 | asserted, asserted, asserted, asserted | 1 |
| `Intuition_2VUsxVJwReb__tL7q4xnt4Jh__TL57ky8oTX7` | candidate_checks_passed | 4 | 4/4 | asserted, asserted, asserted, asserted | 0 |
| `Kinetiq_k8aVPPVguSE__NozCq8ZgtXD__r32n6LxHB36` | candidate_checks_passed | 4 | 1/4 | asserted, asserted, potential, potential | 1 |
| `Merkl_T4ExvutBBXC__KCbBUkDmvZG__9YBmh6mWTAi` | candidate_checks_passed | 1 | 1/1 | potential | 0 |

## 判断

来源格式兼容已在这组报告中正常工作，空 Impact 结果也按规则单独停止。影响项计数达到 28，但只有一半完成 P/I/V；其中多个报告有已提取影响未规则化，公式保真仍需改进。具体要区分清单抽取正确性与规则生成效果，候选通过状态不能代替完整度。

## 产物

- `SELECTION.json`、`manifest_01.json`、`manifest_02.json`：冻结样本。
- `runs/`：报告快照、模型响应、清单、规则及状态。
- `OFFLINE_REPLAY.json`：零模型调用重放结果。
- `FAITHFULNESS_CANDIDATES.json`：公式忠实度盲审诊断。
