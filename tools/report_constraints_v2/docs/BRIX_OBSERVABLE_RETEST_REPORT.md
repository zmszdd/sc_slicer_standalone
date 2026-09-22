# Brix 观察量提示真实复验

日期：2026-09-14。用户授权“真实复验一次”。使用最新通用提示、同一份 Brix 报告，模型 `opencode-go/deepseek-v4-flash`，编号模式、核心范围。实际两次调用，无重试，无手工修补；未发送 PoC、审核卡、参考公式或历史模型答案。第一阶段未修改。

## 结论

**I 的表达在本轮有改善，但正式链路因来源映射缺项被拒绝，不能算复验通过。**

输出：[results/semantic/brix_observable_model_01/](../results/semantic/brix_observable_model_01/)。第一步 10 个实体、21 条陈述，证据编号与结构校验通过。第二步 5 个符号、2 个 claim；持久性 claim 留作 potential、公式 null。请求核心范围不代表程序静默裁剪其他 claim。

状态：`core_formalization_status=failed`、`acceptance_status=rejected`、`external_model_invocations=2`。实际拒绝为 `predicate lacks source mapping`，不是网络异常、超时或 Z3 求解失败。没有生成正式 constraints/SMT/solver-results/stage3-spec；PoC 一致性 `not_evaluated`。

## 核心公式及改善

```text
P = msg_value == buffered_fee && msg_value > fee_native_fee
I = msg_value >= fee_native_fee => !call_reverts_native_mismatch
V = call_reverts_native_mismatch && !lz_message_sent
```

模型本轮自行生成了以上表达，没有看到参考答案。相比上一轮，I 不再用无定义的 excess_tolerated 代表整条性质，P 增加付款等于 helper 结果的关系；特定费用不匹配回退和未发送消息仍保留。

I 限定在 P 下，与审核卡的“不发生特定费用回退”窄义务对应。I 文本还写“excess refunded”，实际公式没有退款约束，模型也明确暂缓退款；不能说整段 I 文字已全部形式化。helper 精确计算、报价时点、完整有效调用条件、代码绑定和更广影响仍未完成。

## 拒绝原因与附加检查

核心 claim：`buffered_overpay_reverts_before_dispatch`。

| 项目 | 缺项 |
| --- | --- |
| P 的来源映射 | 缺 `args.0`（付款等于 helper 结果）、`args.1`（严格多付） |
| I 的来源映射 | 缺 `args.0`（付款不少于报价） |
| 影响覆盖与来源 | `i_buffered_pattern_unusable`、`i_users_cannot_complete_buffered_unstake` 标为 partial，却没有列入 effects.source_ids |

模型给了部分整条公式的根映射，但校验器要求每个相应布尔子公式也有来源。只读重放复现相同拒绝；附加覆盖缺项单独枚举发现，不冒称正式校验器本轮已继续到该步骤。不能仅补三条路径就宣称整体合格。

## 独立数学诊断，不是正式验收

为判断新 I 的窄逻辑是否改善，对原始核心 AST 单独做类型检查和本地 Z3 查询；未修改候选，未生成执行就绪接口，未取消来源检查。人工按候选文字映射特定回退观察量；这是助手审核侧诊断，不是模型自动准确率。

诊断额外限定 `msg_value >= 0`、`fee_native_fee >= 0`、`buffered_fee >= 0`，不写回候选：

- P 可满足：SAT。
- `P && XOR(I, !call_reverts_native_mismatch)`：UNSAT，说明在该抽象 P 下窄 I 等价。
- `P && V && !I`：SAT。
- `P && V && I`：UNSAT。

本轮正式 SMT/Z3 链路未执行；上述是被拒绝候选的独立数学诊断。没有代码转移关系 T，不证明 helper 可达、PoC 一致或报告真实。仍只有一份真实报告，不能给总体准确率或稳定改善结论。

## 用量、校验及归档

第一次 40.699 秒，上报 11,863 tokens；第二次 106.965 秒，上报 31,178 tokens。共 **43,041 tokens**：输入 11,624、输出 6,471、reasoning 24,946，缓存 0。服务 cost 合计 0.0205938，非已核实账单；没有因新提示承诺节省推理开销。

相关 20 项本地回归测试通过；起初一次测试命令在错误工作目录找不到模块，切到模块目录后重跑通过，没有模型重试。受保护的 74 个文件检查通过。原文输入 SHA-256 与历史一致：`5d2a1d54551d336aae12511eb950bbd160f9a7dc340db9bd0e411cc2eec72b97`。

原始结果 SHA-256：

- elements-ids.json：`3a72cedad2aad4f2725882fe94a059b8306fa416aaf17238b94bcafb288a6a63`。
- formalization-ids.json：`4ce1d666ecbbb081a88a3b02c112cb1363501cb323fe16f3cc378fcfc3f04f37`。
- 第一轮 model-response.txt：`cdd0114353e23e830c07b010cead6115ae9f112c72299e933019f1841a2101ea`。
- 第二轮 model-response.txt：`22cf941bd3490390eabe52b7d9800ec589af61b34f86d75a1adcd6f886161e39`。

本轮提示文件 semantic_prompts.py SHA-256：`de63d687184db5eecba7a4ac3688522c01d25f875a9e3e95109c3f5ecb2f2d25`。实际两次 prompt.txt 与原始回答、用量、报告快照均保存在新结果目录。

下一步先做本地改进：明确每个布尔子公式来源路径必须填写，并在模型输出前核对覆盖项与 effects.source_ids 一致。可用这份失败输出补回归测试；任何人工补全另存为助手控制，不算模型成功。不立即追加付费调用，不放宽证据校验。
