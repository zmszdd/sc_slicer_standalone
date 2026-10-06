# semantic-live-2 新报告盲测（5 例）

## 结论

- **工程完成率升至 3/5 候选**（live1 为 2/5），三例全部通过零模型调用的离线
  verify（`prompt_snapshots` 快照重放）。
- **数值门误拒归零**：live1 中 Kinetiq/Intuition 型"叙事性 assumption 数字未
  编码"拒绝本批为 0 例。数值门两次触发（Hybra 显式界被布尔化、Panoptic 自比
  较占位符）都是**正确拦截**——`assumption_numeric_relief` 豁免放行了叙事、
  保住了真约束。
- **要素层保持 5/5 P/I/V 通过、P 含后置观察量 0 例**（live-1 规则在第二批
  未见样本上继续成立）。
- 候选公式严格全通过 2/3；唯一 partial（GTE 的 I）是"指针非零"对"一致性
  更新"的可观测弱化，报告本身无更强编码依据。
- **I 适用条件收窄未复现**：三例候选的 condition 都承载报告的一般性限定
  （任意 bundler/relayer、任意 chainid 变更、任意同价位挂单），未收窄到具体
  事件子场景——live-2 的 I 适用规则在可评样本上成立。
- 2 例拒绝是**新的、更窄的机械族**：两次首次尝试都被门正确拒绝（自比较
  占位符、显式界被布尔化），两次局部修复方向正确（改回显式比较），但
  修复谓词必须改 `pattern`，而 field-scoped 修复把 `pattern` 列为冻结字段 →
  修复被机械丢弃。**离线复核修正**：放行 `pattern` 还不足以救回这两例——
  两个修复后的计划本身仍不满足数值门（见"拒绝归因"），说明剩余瓶颈是
  "界必须用报告字面量常量表达"这一层，而非单纯字段白名单。
- rate 重述规则本批**未被行使**（无报告定义 rate 类量）。

## 样本和规程

- 批次：`prompt_live2_blind_01`，prompt 版本 `semantic-live`（运行时文本 =
  semantic-live-2，sha256 记录于 SELECTION.json，与 live1 批次不同）。
- 冻结：`select.py` 以盐 `stage2-live2-blind-2026-10-06-02:` 做 sha256 排序，
  排除全部历史 case ID（102）、报告哈希（104）、输入哈希（108）（含 live1
  批次全部 5 例），exact_submission、600–4500 字节、每项目一份，选 5 例。
  冻结在模型调用之前，无语义预览。
- 运行：`run_batch.sh` → `main.py batch --prompt-version semantic-live
  --lean-formal-input --continue-on-review`，DeepSeek `deepseek-flash` 直连，
  报告上传与模型调用经用户明确授权（"开始，允许所有授权"）。共 16 次外部
  调用。
- 复核：`SEMANTIC_REVIEW.json`，4 级评分、assistant 复核口径
  （`independent_gold: false`）。Z3 通过不视为语义正确。

## 结果

| 案例 | 工程路由 | 离线 verify | 拒绝原因 |
| --- | --- | --- | --- |
| Intuition | candidate | pass（`prompt_snapshots`） | — |
| GTE Spot | candidate | pass（`prompt_snapshots`） | — |
| Sequence | candidate | pass（`prompt_snapshots`） | — |
| Panoptic | rejected | — | `local repair changed frozen fields` |
| Hybra | rejected | — | `local repair changed frozen fields` |

## 准确性拆分

### 要素层（5/5）

| 维度 | 通过 |
| --- | --- |
| element P / I / V | 5/5 / 5/5 / 5/5 |
| P 中含后置观察量 | 0/5 |

### 公式层（3 例可评）

| 案例 | formula P | formula I | formula V |
| --- | --- | --- | --- |
| Intuition | pass | pass | pass |
| GTE Spot | pass | **partial** | pass |
| Sequence | pass | pass | pass |

GTE 的 I 为 partial：报告的 intent 要求链表指针"一致地更新"，公式编码为
"两个指针非零"——必要但不充分的可观测，且报告没有给出正确邻居身份的依据，
更强编码不可构造。V（P ∧ 两指针均为零）与报告的直接可观测完全一致。

### 拒绝归因（2 例，同一机械族）

| 案例 | 首次尝试被拒原因（正确拦截） | 修复方向 | 修复后仍存在的缺陷（离线复核） |
| --- | --- | --- | --- |
| Panoptic | 自比较占位符 `stored_width == stored_width` | 改为显式界 | `stored_width < 4096`：4096 不是报告文本字面量（文本为 bits [36:48)、12-bit 位宽语义）→ `numeric P literal changed` |
| Hybra | 显式界 `_gaugeType == 1` 被布尔化（`bound hidden`） | 改为显式比较 | `gauge_type == cl_gauge_type_constant` 用符号而非常量 1 表达界 → 仍 `bound hidden` |

两次流程都是：门正确发现缺陷 → 模型修复方向正确 → 修复须改 `pattern`（冻结字段）被拒；且**即使放行**，修复后的计划也过不了数值门。剩余瓶颈定位到两点：(a) 修复通道把 `pattern` 排除在可变字段外；(b) 模型对"界须用报告字面量常量"的表达仍不稳定（位宽 2^N 语义、常量 vs 符号）。

### live-2 三个修复点的验证状态

| 修复点 | 本批观测 |
| --- | --- |
| `assumption_numeric_relief` | **验证**：叙事性 assumption 误拒 0 例；门对真约束照拦 |
| rate 重述规则 | 未行使（批次无 rate 案例） |
| I 适用条件规则 | **成立**：3 例候选无子场景收窄 |

## 工程效率

- 外部调用 16 次（3+4+3+3+3）。超时 0、JSON 格式失败 0。
- 三例候选离线 verify 全部走 `prompt_snapshots`。

## 与历史批次的可比性

不可直接比较：各批报告集不相交、均为 n=5。同口径定性序列（每批的剩余瓶颈）：

- blind_03（v3.20）：要素层 P 缺陷（后置观察量）主导。
- live1（live-1）：要素层净；数值门误伤 assumption + DSL 无除法。
- live2（live-2）：要素层净；数值门不再误伤；剩余瓶颈收窄到
  **field-scoped 修复的 allowlist 不含 `pattern`**。

## 下一步（按本批归因排序）

1. **界的常量表达**（首要）：数值门已把两次布尔化/占位缺陷正确拦下，但模型
   修复时仍不稳定——位宽类界（"12-bit"）被写成 2^12 常量而文本无此字面量、
   枚举界被写成符号常量。方向：formal prompt 补一条"显式界必须用报告文本
   的字面量常量（const）表达，位宽/掩码语义若文本无对应字面量则转入
   unresolved"；修复反馈信息中直接给出期望的常量形式。
2. **修复通道放行 `pattern`**：局部修复的 mutable 字段加入 `pattern`，或改为
   修复后整计划重校验。仅此一项不救回本批两例（见上），但消除"正确修复被
   字段白名单丢弃"这一族。
3. GTE 型 I 的可观测弱化属报告依据上限，暂无 prompt 层动作。
4. rate 规则仍未被行使，留待后续批次自然覆盖。
