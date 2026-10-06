# semantic-live-1 新报告盲测（5 例）

## 结论

- **semantic-live-1 的目标缺陷在本批未复现**：blind_03 归因的首要要素层缺陷（动作产出的后置观察量进入 P）在 5/5 个未见样本中均为 0 例。全部 P 都是动作前状态；先前状态缺乏独立片段支持时，模型改为在 ambiguities 里如实记录而不是断言为 P——这正是新规则要求的行为。
- 工程完成率 2/5 候选，两例均通过零模型调用的离线 verify，且**首次走 `prompt_snapshots` 路径**（活 prompt 快照重放，不依赖 registry 解析当前 `current.py`），证明单文件 live 政策下 run 的可验证性契约成立。
- 3 例拒绝全部发生在形式化阶段，与要素层无关：2 例是**数值保真门误伤叙事性 assumption**（数字已在 P 中编码，仅为复述），1 例是单位门**正确拦截**了一个伪造的派生定义（`expected_rate = total × 1`），其根因是 DSL 缺少除法、无法表达 rate = amount / duration。
- 唯一的公式层缺陷（SukukFi 的 I）是形式化阶段引入的适用范围收窄，**不是要素层继承**——与 blind_03 的归因方向（公式 P 失败全部继承自要素层）形成对照。

## 样本和规程

- 批次：`prompt_live1_blind_01`，prompt 版本 `semantic-live`（活文件 `prompts/current.py`，本批运行时的 element prompt sha256 记录于 SELECTION.json）。
- 冻结：`select.py` 以盐 `stage2-live1-blind-2026-10-06-01:` 对 case_id 做 sha256 排序，排除全部历史 case ID（97）、报告哈希（99）与输入哈希（103），exact_submission、输入 600–4500 字节、每项目一份，选 5 例。冻结在模型调用之前，无语义预览。
- 运行：`run_batch.sh` → `main.py batch --prompt-version semantic-live --lean-formal-input --continue-on-review`，DeepSeek `deepseek-flash` 直连，报告上传与模型调用均经用户明确授权。共 18 次外部调用。
- 复核：`SEMANTIC_REVIEW.json`，沿用 blind_03 的 4 级评分与 assistant 复核口径（`independent_gold: false`）。Z3 通过不视为语义正确。

## 结果

| 案例 | 工程路由 | 离线 verify | 拒绝原因 |
| --- | --- | --- | --- |
| SukukFi | candidate | pass（`prompt_snapshots`） | — |
| GTE Spot | candidate | pass（`prompt_snapshots`） | — |
| Kinetiq | rejected | — | `local repair made no change`（数值门误伤 assumption） |
| Intuition | rejected | — | `local repair made no change`（数值门误伤 assumption） |
| Hybra | rejected | — | `type/unit mismatch`（单位门正确拦截伪造定义） |

## 准确性拆分

### 要素层

| 维度 | 通过 |
| --- | --- |
| element P | 5/5 |
| element I | 5/5 |
| element V | 5/5 |
| P 中含后置观察量 | **0/5** |

要素层 5/5 是本批最重要的观测：新增的 P 时序角色规则（动作产出量不是 P；先前状态须有动作前独立片段，否则记 ambiguities）在 5 个未见样本上均成立。典型例证：

- **Hybra**（新规则的直接靶子）：`p_rollover_accumulated` 是前一周期的合法先前状态，有独立片段确立；blind_03 中出现过的 `_ratio=0` 类后置量不再进 P。
- **SukukFi**：受害者 self-allowance 缺乏动作前的独立片段，模型没有断言它，而是在 ambiguities 里记录“没有片段确立该先前状态”。这正是规则要求的降级行为。

### 最终公式层

仅 2 例可评（候选）：

| 案例 | formula P | formula I | formula V |
| --- | --- | --- | --- |
| SukukFi | pass | **partial** | pass |
| GTE Spot | pass | pass | pass |

SukukFi 的 I 为 partial：报告的一般性要求是 caller≠owner 时必须校验 owner 对 caller 的 allowance，公式把适用条件收窄到“受害者已设 self-allowance 且攻击者零 allowance”的具体子场景（即 P 的两个布尔），未覆盖持有部分 allowance 的 caller。这是形式化阶段引入的范围收窄，方向正确。

### 拒绝归因

| 案例 | 阶段 | 归因 | 性质 |
| --- | --- | --- | --- |
| Kinetiq | 形式化 | `check_numeric_plan` 要求含数字的 assumption 也必须编码为 P 谓词；`asm_front_run_window` 复述的 1h/24h 已编码进 P，模型拒绝重复编码，重试原样返回 | 机械误拒 |
| Intuition | 形式化 | 同族：`assumption_boundary_tx_in_right_block` 的“2 秒出块”是链常量叙事，非约束 | 机械误拒 |
| Hybra | 形式化 | `expected_rate = total_reward_amount × 1` 类型为 HYBR，与声明的 HYBR_per_sec 不等 → 单位门拒绝；正确公式需要除法（`total / period_duration`），DSL 无除法运算 | 正确拦截，根因是表达力缺口 |

**没有一例失败可归因于要素层**；也没有一例可归因于新 P 规则（该规则在本批只改善了行为）。

## 工程效率

- 外部调用 18 次（3+3+4+4+4，含重试）。
- 两例候选的离线 verify 全部走 `prompt_snapshots`：hash 比对 run 目录内 `prompt-element.txt`/`prompt-formal.txt` 与 provenance，并交叉校验快照即首 attempt 发给模型的文本。这是单文件 live prompt 政策的首次端到端验证：live 原地修改后，已完成的 run 仍可精确重放。
- 超时 0、JSON 格式失败 0（DeepSeek 直连 + 严格 JSON 输出在本批稳定）。

## 与 blind_03 的可比性

**不可直接比较**。两批报告集不相交（本批排除 blind_03 全部样本），样本均为 n=5，任何比例差异都不构成统计结论；本报告只用于归因与优先级判断。同口径的定性对照：

- blind_03：要素 P 严格通过 2/5，后置观察量混入 P 是首要缺陷 → 本批 5/5、0 例。
- blind_03：候选 4/5、公式严格全通过 0/4 → 本批候选 2/5、公式严格全通过 1/2（样本更小）。
- blind_03：1 例机械误拒 → 本批 2 例（同族问题在更小样本中比例反而更高，说明数值门对 assumption 的处理仍是系统性弱点）。

## 下一步（按本批归因排序）

1. **数值门对 assumption 的误伤**：`check_numeric_plan` 对含字面量的 assumption 一律要求进 P。应改为——若 assumption 中的数字已被某个 P 谓词的常量覆盖（literal 已编码），或属于链常量/协议常量叙事，则放行并记录。Kinetiq、Intuition 两例即被此修复救回。
2. **DSL 增加除法或 rate 模板**：rate = amount / duration 类关系目前无法表达，模型被迫伪造恒等式。可在表达式语法中加 `div`（固定正除数，与 `mod` 同款约束），或为 value_relation/proportional 类提供带分子的专用模板。
3. **I 适用条件保留**：形式化时 I 的适用范围不应收窄到 P 的具体子场景；prompt 已有方向性自检，需加”适用条件完整性”检查（要素层 intent 的一般性 vs 公式 condition 的具体性）。

## 修复后离线验证（2026-10-06，semantic-live-2）

本节为**事后追加**，不改变上文的冻结结论。三项修复已实现：

1. 数值门豁免（代码，feature `assumption_numeric_relief`，冻结版本均 False）
   ——含字面量但未编码的叙事性 assumption 不再强制进 P；已编码语句的字面量
   保真与 precondition 严格行为不变。
2. rate 重述规则（live prompt）——不新增 DSL 除法：整数除法截断语义会使
   rate 相等产生更弱的 I，且给 `mul` 加单位消除威胁冻结 run 重放；改为
   强制 amount 层重述，无重述时返回 blocking `unsupported_relation`。
   （即对上文”下一步 2”的工程取舍：选了 prompt 规则而非 DSL 扩展。）
3. I 适用条件规则（live prompt）+ 自审第 7 条。

零模型调用的离线证明（
[PROBE_ASSUMPTION_RELIEF.json](PROBE_ASSUMPTION_RELIEF.json)，
[probe_assumption_relief.py](probe_assumption_relief.py) 可重放）：

| 案例 | 严格门（原行为） | 豁免门 |
| --- | --- | --- |
| Kinetiq | `numeric P source missing from plan` | 数值门通过，合成通过 |
| Intuition | `numeric P source missing from plan` | 数值门通过，合成通过 |

冻结 run 产物未改写；live1 两个候选改动后 verify 重放仍为
`offline_verified: true`（走 `prompt_snapshots`）。Hybra 的 rate 规则与
SukukFi 的 I 适用规则是 prompt 行为改动，只能在新授权的冻结盲测批次上
测量效果。
