# semantic-v3.20 冻结留出集测量（与 v3.16 同一批 5 例）

## 结论

在这批 5 例上，v3.20 的**工程完成率与 v3.16 相同（3/5）**，**误拒绝由 1/5 降为 0/5**，
三项全忠实的候选由 **1/5 升到 2/5**。

但这个提升**不是公式忠实度的提升**：它完全来自"原先不可评的一例（Intuition 误拒绝）变为
忠实候选"，即**可用性提升**。**没有任何一例的公式忠实度得到改善**——Merkl 的核心缺陷
（义务条件被 P 事实污染）在 v3.16 与 v3.20 **语义上逐字相同**。

同时得到一条结构性结论：对 `relation_obligation` 编码，编译出的
`V = condition ∧ ¬(I 的后件)`，因此 `P ∧ V ∧ I` **构造性地不可满足**。
"严格 P/I/V 门"（`strict_piv_gate`）对这类编码**不含信息**，不能当作忠实度证据。
v3.20 把 Merkl 从 `review` 升为 `candidate`，并把 v3.16 原有的覆盖率告警一并消除，
缺陷因此**对自动层不可见**。

本报告是助手自评产物（`reviewer_kind = assistant_artifact_review`，`independent_gold = false`），
n = 5，不得外推为总体准确率。评测未使用也未要求 `gold_v1` 审批。

## 冻结与输入

- 输入：沿用 `evaluation/prompt_v316_holdout_01/` 的**同一 5 份冻结报告**（均为此前未见、
  未参与 prompt 设计的同提交匹配报告）。
- 调用参数与 v3.16 运行**逐项一致**：`report-json-input/4`、`deepseek-flash`、
  `lean_formal_input`、`element_retries 1`、`formal_retries 2`、`continue_on_review`、
  `case-dir` 调用（含配对校验）。
- **输入可复现性**：5/5 例的 `report_input_sha256` 与冻结 `SELECTION.json` 记录**逐字节一致**。
- 唯一变量：`--prompt-version semantic-v3.20`。
- 单次运行，未挑样、未修补；诊断性重跑另存 `runs_transport_retry/`，**不计入**下表。

## 工程结果（规程第 2 步，全自动）

| 案例 | 步骤0 输入充分 | 第一步 要素 | 第二步 形式化 | SMT | 调用 | 秒 | tokens | 路由 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GTE Perps and Launchpad | ready | 完成 | 失败 | — | 5 | 18.3 | 26,556 | `pipeline_failure` |
| Merkl | ready | 完成 | 完成 | 完成 | 3 | 11.8 | 12,800 | `candidate` |
| Intuition AtomWallet | ready | 完成 | 完成 | 完成 | 3 | 12.5 | 12,202 | `candidate` |
| Sequence Transaction Rails | **畸形 JSON** | 未运行 | 未运行 | — | 1 | 1.8 | 1,283 | `pipeline_failure` |
| SukukFi | ready | 完成 | 完成 | 完成 | 3 | 9.9 | 10,144 | `candidate` |
| **合计** | 4/5 | 4/5 | 3/5 | 3/5 | 15 | 54 | 62,985 | candidate 3 / pipeline_failure 2 |

- 自动覆盖率（candidate / 全部）= **3/5 = 60%**。
- `pipeline_failure` **2/5，单列**，未并入拒绝，也未计入弃权。
- 步骤0 与第一步各差 1 例：Sequence 的**输入充分性调用**返回畸形 JSON（1178 字符，
  completion 350 tokens）。该调用提示词与 v3.16 运行**字节相同**（sha256 `2aefda02...`），
  而同一提示词在 v3.16 返回 1403 字符并可解析 → **抽样波动**，与 v3.18–v3.20 的改动无关。
  要素/形式化阶段有重试，**输入充分性调用没有重试**，故单次畸形即为硬失败。

## 语义复核（规程第 3 步）

抽样全评 3 个候选（`unknown` = 0/3）：

| 案例 | 要素 P/I/V | 公式 P | 公式 I | 公式 V | 判定 |
| --- | --- | --- | --- | --- | --- |
| Merkl | pass/pass/pass | **fail** | **fail** | **fail** | 条件被 P 事实污染，I 在攻击状态空洞 |
| Intuition AtomWallet | pass/pass/pass | pass | pass | pass | 三项忠实 |
| SukukFi | pass/pass/pass | pass | pass | pass | 三项忠实 |

- 候选语义错误率（全部维度）：**1/3 = 33%**（Merkl）。
- 逐维错误率：P 1/3、I 1/3、V 1/3（同一例）。
- 三项全忠实：**2/3**。
- **要素层 4/4 全为 pass/pass/pass**（含 GTE），再次明显优于公式层。

### Merkl：公式层缺陷的精确定位

- **要素层是对的**：I = `operator_should_not_fund_campaign`（"operator 的钱包不应被扣款"），
  V = `bob_funds_campaign`（"1000 USDC 直接从 Bob 钱包扣走"）。
- **公式层把 P 事实塞进了义务的条件**：条件含 `creator_internal_balance >= campaign_amount`
  （来源 `alice_deposits_1000_usdc`）。而报告的攻击**正是靠该比较为假**——原文
  `if (0 >= 1000)` 判假才走 fallback 从 operator 扣款。
- 因此该条件**恰好排除了攻击状态**：I 在那里空洞为真，V 也无法与攻击共存。
  P 同样断言了这个被攻击否定的比较。
- 结论：**P/I 角色混淆**（把一条 P 来源用作义务的触发条件）。
- v3.16 也判 fail/fail/fail；v3.20 修好了表面缺陷（重复 P 塌缩、覆盖率抱怨），
  **但 I 反而丢失了数值信息**（v3.16 的 I 含 `operator_paid_amount = 0` 与
  `creator_funded_amount = campaign_amount`，v3.20 退化为单个布尔 `¬operator_charged`）。

## 与 v3.16 对比（同一批 5 例，同一冻结集）

| 指标 | v3.16 | v3.20 |
| --- | --- | --- |
| 步骤0 输入适宜 | 5/5 | 4/5（抽样波动；屏幕调用无重试） |
| 第一步 要素有效 | 5/5 | 4/5（同上；要素提示词自 v3.16 起未变） |
| 工程完成（产出候选） | 3/5 | 3/5 |
| 误拒绝 | 1/5 | **0/5** |
| 三项全忠实的候选 | **1/5** | **2/5** |
| 语义错误的候选 | 1（Merkl） | 1（Merkl，同一缺陷） |

**提升全部来自可用性（一例误拒绝被修复），没有一例的公式忠实度改善。**
要素层两版之间的差异属抽样波动，因为要素提示词与代码自 v3.16 起未改动。

## 效率

15 次模型调用、54 秒、62,985 tokens（v3.16 为 20 次调用、115.67 秒、88,093 tokens）。

## 后续问题

1. **义务条件不得由 P 事实播种**：`relation_obligation` 的条件若含一条被报告攻击所否定的
   P 事实，义务即被假设掉。这正是 v3.21 `semantic_axioms` 计划中的
   "P 时间角色检查" 与 "impact↔relation 模板一致性门"要拦的情形。
2. **`P ∧ V ∧ I` 对这一类编码恒不可满足**，`strict_piv_gate = true` 不构成忠实度证据；
   自动层需要一条**非平凡**的紧致性判据（否则 v3.20 这类"缺陷不可见"会重现）。
3. **输入充分性调用没有重试**：单次畸形响应即成为硬 `pipeline_failure`。建议与该阶段其余
   调用一样允许一次重试（仅此一处，属同文件同功能改动）。
4. **GTE 未修复**：三次尝试均为"数值 P 遗漏 / 局部修复无改动"，与 v3.16 同源；
   局部修复返回"无改动"仍计一次失败，值得单独诊断。
5. **n = 5 且为助手自评**，不构成总体准确率；需要更大规模、分层的独立复核才能给出总体数字。
