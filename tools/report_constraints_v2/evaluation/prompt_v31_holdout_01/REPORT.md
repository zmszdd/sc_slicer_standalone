# semantic-v3.1 真实留出集测评

日期：2026-09-15。状态：真实模型运行、离线重放和助手初评完成；尚未经用户或独立专家确认。

## 结论

v3.1 成功缩短了提示和模型正常返回时的 JSON，但**没有达到准确提取 P/I/V 的目标**。

因此真实测评后没有将 v3.1 保持为默认；当前入口默认切回 `semantic-v3`，v3.1 仅作为显式可选实验保留。

- 5 个此前未用于提示开发的项目，实际调用 9 次，无重试。
- 第一调用完成 4/5；Ekubo 在第一次调用超时。
- 第二调用产生 3 份可保存回答；Blackhole 在第二次调用超时。
- 正式管线完成 1/5（Monetrix），但其 I/V 语义仍只评为 partial。
- 正式 I：0 pass、2 partial、3 fail。
- P/I/V 六维全部 pass：0/5。
- 排除 formal I 后，五个定性维度严格 pass 14/25，即 56%；这是助手评分单元率，不是总体准确率。

## 分案例

| 案例 | P | 自然语言意图 | 正式 I | V | 管线结果 | 核心问题 |
| --- | --- | --- | --- | --- | --- | --- |
| Blackhole circulating supply | partial | pass | fail | pass | 第二步 timeout | 用“50%”代替精确余额关系；添加错误/无依据的下溢假设 |
| Ekubo Transfer event | fail | fail | fail | fail | 第一步 timeout | 没有模型候选，按预设规则留在分母 |
| Intuition validity window | pass | pass | fail | pass | schema rejected | 漏掉 `formula_sources`，并用自由 `window_bound` 布尔量承担部分 I |
| Monetrix net backing | pass | pass | partial | partial | needs_review | 把 `total==supply-borrow` 弱化为 `total<=supply-borrow`，V 未表达恰好高估 borrow |
| Olas TWAP | partial | pass | partial | partial | modality rejected | P 未固定零 slippage/真实偏差；V 不保证违反 I；potential 被升级为 asserted claim |

逐项理由与候选哈希见 [ratings.json](ratings.json)，冻结参考见 [REFERENCE.md](REFERENCE.md)，机器重放结果见 [metrics.json](metrics.json)。原始输出保存在 `../../results/semantic/prompt_v31_holdout_model_01/`。

## 与 v3 的关系

v3 使用另一批五报告：4 个案例超时、1 个正式 I 初评 pass。v3.1 本批只有 2 个案例超时，且有 3 份第二步回答落盘，但两份被严格规则拒绝，唯一通过结构检查的公式又发生语义弱化，最终正式 I 为 0 pass。

两批报告不同，模型服务的 token 统计行为也不同，因此不能宣称 v3.1 因果性降低了超时或降低了准确率。可以客观确认的是：**在本批上，输出预算改善了部分可返回性，但没有改善最终 P/I/V 可用率。**

## 成本与验证边界

已保存的 7 个 usage 文件共记录 82,696 tokens、估算成本 0.0380337；两个超时调用没有 usage 文件，故不是完整账单。较短 Prompt 不代表模型 reasoning token 必然减少。

Z3 只在 Monetrix 的报告规范上运行，证明其 P/I/V 公式内部关系可求解；不能证明公式语义正确，也没有代码执行关系 T。本批没有向模型发送 PoC、预设参考或历史答案，没有修改第一阶段、`semantic_core.py`、`report_only.py`、Z3/SMT 校验器、Rust/Solar 或 `run.sh`。

## 下一步

不应继续盲目压缩。下一版只针对已观察的四类错误做 v3.2：

1. schema 最终检查明确要求 claim 精确包含 `formula_sources`，不得漏字段或增字段。
2. 任何 `impact_id` 为 potential 时，claim 必须为 potential。
3. 报告说“等于/恰好”时必须使用 `eq`，不得弱化为 `le/ge`。
4. V 必须直接包含使 I 为假的观察关系；若做不到则 `null + unresolved`，不能用 root-cause 等式冒充 V。
5. P 优先采用报告给出的最窄可表达数值场景，例如 `slippage=0`，而不是引入缺少单位定义的一般公式。

这些修改应保持当前预算，不增加示例目录、漏洞规则、重试或调用次数。之后只能在另一批新报告上评估泛化；当前留出集只作为失败回归。

离线重放：

```bash
cd /root/sc_slicer_standalone/tools/report_constraints_v2
/root/.local/share/uv/tools/halmos/bin/python \
  evaluation/prompt_v31_holdout_01/evaluate.py
```
