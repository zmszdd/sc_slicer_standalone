# Brix 核心模式真实复验

日期：2026-09-14。用户明确授权本轮向 `opencode-go/deepseek-v4-flash` 发送同一 Brix 报告编号片段及第一步要素，最多两次调用、不重试、不发送 PoC、审核卡或参考公式。实际两次调用，原始回答未修补，第一阶段未修改。

## 结论：程序链路首次真实跑通，语义候选仍待改进

```text
原报告 → 编号要素提取 → 约束候选 → 完整校验/SMT → 本地 Z3
       → 文件和反例只读重放通过
```

输出在 [results/semantic/brix_fee_ids_core_model_01/](../results/semantic/brix_fee_ids_core_model_01/)。返回状态：`core_formalization_status=formalized_candidate`、`acceptance_status=needs_review`、`consistency_verdict=not_evaluated`。退出码 2 表示需要审核，不是运行异常或被拒绝；完整规范与求解文件已生成。

第一步 7 个实体、21 条陈述；第二步 6 个符号、1 个 claim。核心 claim 没有混入 potential 的持续影响；其余影响保留在 elements、limitations 及 unassigned_impact_ids，部分/缺失覆盖仍触发 needs_review。没有因聚焦核心而宣称整个报告已覆盖。

## 对照审核卡的结果

本节为助手按用户确认的初步语义基准复核，不是独立专家评分或准确率百分比。

- P 改善：保留 `buffered_flow_used && msg_value > native_fee`，不再放宽成 `>=`。helper 计算、付款与 helper 结果的一致性仍主要依赖语义描述/文字假设，没有完整数值约束。
- V 改善：`paynative_reverted && !message_dispatched`，回退符号明确指 _payNative 的 NotEnoughNative，不再只是任意 unstake 回退。全体/持续影响仍没有完整建模。
- 模态改善：持续失败留作 potential 的暂缓影响，没有将其混入 asserted 核心 claim；这是单次结果，不能证明稳定提高。
- **I 仍不充分：公式只有独立布尔量 `excess_tolerated`。** 其自然语言意思是“应容忍多付”，但没有 AST 定义把它与 `!paynative_reverted` 关联；描述文字不自动成为 SMT 约束，也还混有“可退款”意图。因此没有忠实完成审核卡中可检验的核心安全义务。

## Z3 暴露的缺口

6 项查询都为 SAT，包括 `P ∧ V ∧ ¬I` 和 `P ∧ V ∧ I`。后者有如下数学赋值：

```text
msg_value=1, native_fee=0, buffered_flow_used=true,
excess_tolerated=true, paynative_reverted=true, message_dispatched=false
```

也就是公式允许“容忍多付=true”和“发生特定回退=true”同时成立。模型文字声称回退违反 I，但公式未表达这种关系。`P ∧ V ∧ ¬I=SAT` 不能单独证明推导准确；独立的 I 可以任意取 false。

现有关系检查未对此返回 warning，因为它主要检查坏效果是否完全不能违反 I；当前 I 自由变量使两种情况都可满足。`no_relationship_warning` 不是语义正确的结论。整体仍待人工审核、不可执行就绪。

这些是规范层数学状态，不是实际 PoC 路径。金额使用无界数学整数，未加完整非负/EVM 域；该赋值中的 0/1 也不证明真实 helper 能产生该付款。无代码 T，没有漏洞真伪或一致性结论。

## 复核、用量及归档

原报告及输入 SHA 与历史轮一致。`verify_semantic.py` 只读复核通过：原始模型候选、编号解析、规范重编译、查询状态、SMT 哈希及保存反例均可重放。新增 [semantic-review.json](../results/semantic/brix_fee_ids_core_model_01/semantic-review.json)记录审核意见及原始回答哈希，不修改既有结果文件。

两次模型上报共 **35,297 tokens**：输入 10,865、输出 5,238、reasoning 19,194、缓存读写 0；第一步 37.843 秒，第二步 81.788 秒。服务 cost 字段合计 0.01628895，不当成已核实账单。比上一轮上报 token 少，但模型输出和推理随机性不同，不能归因于核心模式或保证以后节省。保护检查 74 个文件未变，本轮无额外模型重试。

## 下一步

不要扩大批量或修改原始 I。优先防止把整个安全义务命名成没有定义的自由布尔符号：符号应是能绑定到代码的观察量，推导性质应在 AST 中组合观察量；若使用派生谓词，必须有可检查的定义，否则标记待审核。按审核卡，核心义务需要表达限定 P 下不得发生费用不匹配回退；退款意图另行处理。

另补全金额域及必要付款关系，并加强“坏效果与 I 同时成立”的关系审核。这只是诊断提示，不是对所有报告强制 `P ∧ V ∧ I=UNSAT`，因为弱性质/部分效果也可能同时成立。改进后先做本地对照测试，再单独申请有预算的真实复验。本轮只验证和记录，不改变底层校验逻辑。

复跑本次输出（零模型调用）：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_semantic.py \
  tools/report_constraints_v2/results/semantic/brix_fee_ids_core_model_01
```

## 后续本地改进：观察量表达及审核提示

用户授权后已实施，外部模型调用为零：

- 通用提示要求符号是输入、状态或执行结果，不是期望；I 应组合观察量。派生谓词必须展开成定义 AST，含义/推导文字不充当 SMT 约束；定义缺失用 null/unresolved，不引入代表整条性质的自由布尔量。
- 新增 `review_observability.py`，检查仅出现在 I 的布尔符号及坏效果允许 I 两种真假值的情况。它只触发需要定义或人工绑定审核，不根据变量名字猜语义，不一律拒绝 I-only 布尔观察，也不强制所有报告 `P∧V∧I=UNSAT`。
- 新输出保存 `observability-review.json`，纳入 bundle、审核状态和第三阶段接口哈希；有提醒时保留 needs_review。候选 AST 和原求解逻辑不改变。重放器对新文件重新计算提示及校验哈希；旧历史包仍走原有兼容路径。

### 零调用对照实验

旧真实模型包只读审核，准确标出 `excess_tolerated` 和两个 I 真值都可与坏效果共存的问题。原始模型输出不改写。

另存助手来源的表达控制样例：复用同份报告和真实第一步要素，以用户已审核的窄安全义务，将 I 表达为限定 P 下的 `!paynative_reverted`，移除独立旗标；P、V、影响覆盖和暂缓影响保持原样，未添加 helper 算术或 EVM 模型。候选保存于 `samples/brix_observable_control_01/`，结果保存于 `results/semantic/brix_observable_control_01/`，均明确标记 assistant_review，不算模型自动准确性的成绩。

结果：`P∧V∧¬I=SAT`、`P∧V∧I=UNSAT`，观察量结构检查不再产生提醒，完整文件/查询/反例重放通过。整体仍 needs_review，因为更广影响、文字假设和代码绑定未完成；不能解释成已证明真实 helper 可达、PoC 一致或报告真实。

119/119 V2 回归测试通过（新增 10 项），覆盖旧旗标提示、合法独立观察的保守处理、公式不变、观察量控制、历史兼容、新审核文件篡改等。保护检查 74 个文件未变。

只读检查旧真实候选：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/review_observability.py \
  tools/report_constraints_v2/results/semantic/brix_fee_ids_core_model_01
```

复核助手对照包：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_semantic.py \
  tools/report_constraints_v2/results/semantic/brix_observable_control_01
```

下一步如需验证模型是否自行改善，仍要单独进行有预算的真实复验，不能将助手对照公式发送给提取模型；本轮未做该调用。
