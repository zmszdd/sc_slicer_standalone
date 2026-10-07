# semantic-live-3 新报告盲测（10 例）

## 结论

- **工程完成率 6/10 候选**（live2 为 3/5，同为 60%，但样本翻倍），六例全部通过
  零模型调用的离线 verify（`prompt_snapshots` 快照重放）。
- **live-2 的常量表达拒绝族被消除**：live2 拒绝的 Panoptic 家族新案例
  （Panoptic__Next_Core）本次经"门拦下首次缺陷 → 修复通道改写谓词 → 通过"
  成为候选——三项 live-3 修复（常量字面量规则、修复反馈处方、pattern 放行）
  在其目标族上联合生效。接受的计划中全部界常量（1000、1000000）均为报告
  文本字面量。
- **要素层 9/9 可评全过、P 含后置观察量 0 例**；Kinetiq 在输入筛查层诚实
  弃权（报告无可检的安全关系依据），无要素产物。
- 公式层 6 例可评：**I/V 全部 6/6 严格通过**；公式 P 4/6，两例 partial 是
  同一缺陷形态——两个不同要素事实共用一条重复 truth 谓词，其中一条事实
  塌缩未被表示（`identical_p_predicates` 的"报告不拒绝"设计正好把它暴露
  出来）。
- 4 例拒绝归因：**1 例误伤 + 2 例正确拦截 + 1 例诚实弃权**。无一属于 live2
  的常量表达族。数值门对叙事性 assumption 误伤连续第二批为 0。
- 修复了 verify 的一个重放缺陷：要素层发生重试的 run，重放比对必须用最后
  一次 neural-elements 尝试（此前必误报 `neural elements changed`）。

## 样本和规程

- 批次：`prompt_live3_blind_01`，prompt 版本 `semantic-live`（运行时文本 =
  semantic-live-3，sha256 记录于 SELECTION.json）。
- 冻结：`select.py` 以盐 `stage2-live3-blind-2026-10-06-03:` 做 sha256 排序，
  排除全部历史 case ID / 报告哈希 / 输入哈希（含 live1/live2 全部 10 例及
  终局保留批 final_holdout_01 的 10 例——保留批经 SELECTION.json 扫描自动
  排除，两批样本不相交）。exact_submission、600–4500 字节、每项目一份，
  选 10 例、拆两个 manifest（批运行器单 manifest 上限 5 例）。
- 运行：`run_batch.sh`（含 `--resume`，第二个 manifest 复用 runs/ 目录），
  `main.py batch --prompt-version semantic-live --lean-formal-input
  --continue-on-review`，DeepSeek `deepseek-flash` 直连。共 35 次外部调用
  （6+4+3+4+3+3+4+4+1+3）。超时 0、JSON 格式失败 1（Intuition 首次尝试）。
- 复核：`SEMANTIC_REVIEW.json`（assistant 主复核，`independent_gold:
  false`）+ `DUAL_REVIEW.json`（同模型 deepseek-flash 异构审计 prompt 双
  复核）。Z3 通过不视为语义正确。

## 结果

| 案例 | 工程路由 | 离线 verify | 备注 |
| --- | --- | --- | --- |
| GTE_Perps | candidate | pass（`prompt_snapshots`） | 公式全过 |
| Panoptic_Hypovault | candidate | pass | 公式 P partial（重复谓词） |
| SukukFi | candidate | pass | 公式全过；I 含授权限定 |
| Panoptic__Next_Core | candidate | pass | live2 拒绝族的家族案例被救回；公式 P partial（重复谓词） |
| Merkl | candidate | pass | 公式全过；1000 为文本字面量 |
| Brix_Money | candidate | pass | 公式全过；窄化在 unresolved/limitations 如实记录 |
| Monetrix | rejected | — | 数值门误伤：`0x811` 十六进制协议常量 |
| Hybra | rejected | — | 正确拦截：伪造单位乘积定义；修复原样返回 |
| Intuition | rejected | — | 正确拦截：伪造 curve 恒等式；首次尝试 JSON 格式失败 |
| Kinetiq | needs_input_review | — | 输入筛查诚实弃权（safety_relation_basis 缺失） |

## 准确性拆分

### 要素层（9 例可评）

| 维度 | 通过 |
| --- | --- |
| element P / I / V | 9/9 / 9/9 / 9/9 |
| P 中含后置观察量 | 0/9 |

### 公式层（6 例可评）

| 案例 | formula P | formula I | formula V |
| --- | --- | --- | --- |
| GTE_Perps | pass | pass | pass |
| Panoptic_Hypovault | **partial** | pass | pass |
| SukukFi | pass | pass | pass |
| Panoptic__Next_Core | **partial** | pass | pass |
| Merkl | pass | pass | pass |
| Brix_Money | pass | pass | pass |

两个 partial 的机制：两个不同的已选前置事实映射到同一条 truth 谓词
（如 `tiny_total_assets`、`wallet_initialized`），合取塌缩后其中一条
报告事实不再被表示。该检查在 schema/4 下有意"报告不拒绝"（保冻结
重放），verify 输出中可见——缺陷可见、产物可重放。

### 拒绝归因（4 例）

| 案例 | 首次被拒原因 | 定性 |
| --- | --- | --- |
| Monetrix | `numeric P source missing`：前置叙事含 `0x811`（协议槽位数），字面量扫描把 811 计为数字 | **误伤**：机制常量被当语义界。n=1 新族，按吝啬门槛（≥2 例才进 prompt 规则）暂记暂缓 |
| Hybra | `type/unit mismatch`：`expected_victim_shares = deposit × totalSupply` 定义后与纯 shares 比较 | **正确拦截**：忠实形式是交叉相乘关系（本批 Panoptic_Hypovault 证明模型能写出）。修复原样返回是模型修复纪律失败 |
| Intuition | `type/unit mismatch`：伪造 `total_assets = 因子 × …` 恒等式 | **正确拦截**：报告无此定义；门的存在意义。首次尝试另有 JSON 格式失败（工程噪声） |
| Kinetiq | 输入筛查 `uncertain`（`safety_relation_basis` 缺失） | **诚实弃权**：报告无可检安全关系，筛查层如实拒绝，无产物可评 |

## live-3 修复点验证状态

| 修复点 | 本批观测 |
| --- | --- |
| 界常量字面量规则 | **生效**：接受计划全部界常量来自文本；live2 拒绝族救回 1 例 |
| 修复反馈常量处方 | **生效**（与上一条联合作用，无法单独归因） |
| pattern 放行 | **生效**：Panoptic__Next_Core 修复改写谓词后通过字段校验 |
| assumption_numeric_relief（live-2 引入） | 连续第二批误伤 0 |

## 工程效率

- 外部调用 35 次；超时 0；JSON 格式失败 1。
- 发现并修复 verify 缺陷（要素重试 run 的重放比对取首次而非最后一次尝试，
  [batch_verify.py] 现取最后一个 `neural-elements-retry-*`）。
- 双 manifest 批运行需要第二个 manifest 带 `--resume`（输出目录已存在），
  run_batch.sh 已固化。

## 与历史批次的可比性

不可直接比较（各批报告集不相交）。同口径定性序列（每批的剩余瓶颈）：

- blind_03（v3.20）：要素层 P 缺陷（后置观察量）主导。
- live1（live-1）：数值门误伤 assumption + DSL 无除法。
- live2（live-2）：常量表达层（界须用文本字面量）+ pattern 冻结。
- live3（live-3）：**常量表达族清零**；剩余为 (a) 伪造单位/恒等式定义
  （type/unit 族，live1 即存在），(b) 十六进制协议常量误伤（n=1），
  (c) 重复谓词塌缩（报告可见、不拒绝），(d) 修复纪律（原样返回）。

## 双复核（同模型异构 prompt）

见 `DUAL_REVIEW.json`（deepseek-flash，审计口径 prompt，与生成 prompt 结构
不同）。结果与主复核的分歧点将逐条列出。

## 下一步（按本批归因排序）

1. **停止规则检查**：live-3 相对 live-2 无工程完成率提升（60%→60%），但
   拒绝族发生迁移且 live-3 修复点全部验证生效、要素层连续两批干净。
   按约定（最多 2 轮迭代），**live-4 是最后一轮**，其目标是 (a) 重复谓词
   塌缩（prompt 自审第 3 条已禁自比较，可扩为禁重复谓词）与 (b) 修复
   纪律（原样返回）。若无实测改善则停，进入终局保留批 n=10 测量。
2. 十六进制协议常量误伤：n=1，暂缓；若 live-4 复现（凑满 ≥2 例）再修
   （方向：PLAIN_NUMBER 对 `0x` 前缀十六进制按协议标识处理，或 element
   层指引把机制常量叙事归 assumption）。
3. type/unit 伪造定义族：已有正确拦截；改进方向是修复通道教模型改写为
   交叉相乘（修复反馈已有类似处方，可在 live-4 强化一句）。
