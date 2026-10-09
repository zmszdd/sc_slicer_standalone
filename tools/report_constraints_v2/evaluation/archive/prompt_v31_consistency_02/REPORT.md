# semantic-v3.1 第三批：错误一致性复测

日期：2026-09-15。状态：真实模型调用、离线重放和助手初评完成；未经用户或独立专家确认。

## 结论

当前问题具有**部分一致性**：语义错误会跨新案例重复，但超时和 schema 错误不是每批必现。

- 5 份新 finding，10 次调用，无重试、无超时。
- 5/5 产生要素，5/5 产生形式化回答。
- 4/5 通过结构校验进入 `needs_review`；Olas 因模态升级被拒绝。
- 正式 I：3 pass、1 partial、1 fail，初评 60%。
- 完整 P/I/V 六维均 pass：1/5（Sequence）。
- 排除 formal I 后，五个定性维度严格 pass 17/25，即 68%；不是总体准确率。

## 重复出现的错误

| 错误类型 | 本批 | 与上一批关系 | 判断 |
| --- | ---: | --- | --- |
| P 缺失或混入实现结果 | 3/5 | 上一批也有 Blackhole/Olas | 持续问题 |
| I 强度或范围错误 | 2/5 | 上一批存在等式弱化/自由布尔 | 持续问题 |
| V 不能保证 `not I` | 2/5 | 上一批 Olas TWAP 已出现 | 明确重复 |
| potential 升级为 asserted | 1/5 | 上一批也是 1/5 | 明确重复，但两次均来自 Olas，存在项目写作风格相关性 |
| schema 漏/增字段 | 0/5 | 上一批 1/5 | 未稳定复现 |
| timeout | 0/5 | 上一批 2/5 | 服务/案例相关，不是本批稳定错误 |

因此可以确认：**P 完整性、V/I 逻辑关系和模态保持是 Prompt 本身需要优先修复的问题**。仅增加超时或重试不能解决这些语义错误。

## 分案例

| 案例 | P | I | V | 限定/模态 | 结果 |
| --- | --- | --- | --- | --- | --- |
| Panoptic BuilderWallet | fail | fail | partial | pass | P 漏 unauthorized/initialized；V 与 I 可共存 |
| Sequence domain fork | pass | pass | pass | pass | 本批唯一完整 P/I/V 初评通过 |
| Ekubo swap deadline | partial | pass | fail | pass | V 只有 user loss，未包含晚执行；程序确认 V 与 I 可共存 |
| Intuition pause | partial | partial | pass | partial | P 混入入口仍 live；未保留 withdraw 可能例外 |
| Olas sweep | pass | pass | pass | fail | potential impact 再次被升级为 asserted claim |

其中 Panoptic 与 Ekubo 的自动观察量审查也分别给出 `effects can coexist with either safety truth value under P`，与人工判断一致。这说明现有本地关系检查能发现一部分 V/I 错误，但仍只产生审核提醒，不能自动修补或宣告语义正确。

逐项评分与候选哈希见 [ratings.json](ratings.json)，预先参考见 [REFERENCE.md](REFERENCE.md)，机器指标见 [metrics.json](metrics.json)。原始结果位于 `../../results/semantic/prompt_v31_consistency_model_02/`。

## 与上一批 v3.1 的解释

上一批正式 I 为 0 pass、完整 P/I/V 为 0/5；本批为 3/5 和 1/5，且超时由 2 降为 0。由于报告不同、样本小、项目写作风格相关、模型生成具有随机性，不能认为 Prompt 的准确率突然提高。两批差异反而说明单次五报告比例方差很大，需要人工 gold 和更多固定样本。

两批共同支持的结论不是某个准确率数字，而是错误排序：

1. P 条件角色和完整性。
2. 强制 V 在 P 下违反 I。
3. claim 模态必须由所含最弱 impact 决定。
4. 保持 I 的精确强度与范围。

## 成本和边界

10 个 usage 文件共记录 107,207 tokens、估算成本 0.04771075；这不是经账单核验的费用。模型未收到 PoC、预设参考或历史答案。Z3 只检查报告规范内部逻辑，不检查代码 T。本轮不修改 Prompt、第一阶段、底层校验器或历史输出。

完整 P/I/V 仍只有 1/5，因此 v3.1 继续保持实验状态，默认入口仍为 v3。下一步可以依据重复错误设计 v3.2，但不应再对本批调参后将其作为泛化测试。

离线重放：

```bash
cd /root/sc_slicer_standalone/tools/report_constraints_v2
/root/.local/share/uv/tools/halmos/bin/python \
  evaluation/prompt_v31_consistency_02/evaluate.py
```
