# semantic-live-4 盲测（10 例，最终迭代轮）

## 结论

- **工程完成率 6/10 候选**（live2 3/5、live3 6/10、live4 6/10——连续第三批 60%），
  六例全部通过零模型调用的离线 verify（`prompt_snapshots` 快照重放）。
- **live-3 的最大拒绝族（type/unit 伪造定义）消失**：live-3 因此族被拒的
  Hybra/Intuition 项目新实例本次全部成为候选；Intuition 首次尝试仍是
  `type/unit mismatch`，经修复通道改写为交叉相乘关系后通过——live-4 新增的
  交叉相乘处方在其目标族上生效（零伪造派生符号）。
- **live-4 的两个 prompt 目标一成一败**：交叉相乘处方生效（如上）；重复谓词
  禁令未生效——Hybra 仍把两个不同要素事实塌缩到同一条
  `rhybr_address == zero_address` 谓词（报告可见、不拒绝，与 live-3 同形）。
- 公式层 6 例可评：V 全部 6/6 严格通过；P 4/6、I 4/6（各两例 partial，归因
  见下）。要素层 10/10 可评，I/V 全过，P 一例 partial（GTE_Perps 把攻击动作
  与其结果状态捆绑成一条前置叙述）。
- 4 例拒绝归因：**1 例误伤（hex 协议常量 `0x811`，第二个独立案例，族门槛
  ≥2 已凑满）+ 2 例正确拦截（单次修复已朝正确方向移动但重试预算耗尽）+
  1 例修复纪律失败**。
- 按预注册方向应用了 hex 误伤修复（`0x` 前缀常量按协议标识处理，不再计为
  数值字面量；真正的十六进制界仍由 bounds 扫描强制）。离线解锁证明
  （HEX_UNLOCK_PROBE.json）：Monetrix 被拒计划在修复后通过数值门并可合成
  形式化——被拒记录不变，证明该拒绝确为误伤而非计划缺陷。

## 样本和规程

- 批次：`prompt_live4_blind_01`，prompt 版本 `semantic-live`（运行时文本 =
  semantic-live-4，sha256 记录于 SELECTION.json）。
- 冻结：`select.py` 以盐 `stage2-live4-blind-2026-10-07-01:` 做 sha256 排序，
  排除全部历史 case ID / 报告哈希 / 输入哈希（含 live1/live2/live3 全部案例
  及终局保留批 final_holdout_01——保留批经 SELECTION.json 扫描自动排除）。
  exact_submission、600–4500 字节、每项目一份，选 10 例、拆两个 manifest。
- 运行：`run_batch.sh`（`--resume`），`main.py batch --prompt-version
  semantic-live --lean-formal-input --continue-on-review`，DeepSeek
  `deepseek-flash` 直连。共 40 次外部调用（8×4 + Panoptic_Hypovault 3 +
  Panoptic__Next_Core 5）；超时 0、JSON 格式失败 0。
- 复核：`SEMANTIC_REVIEW.json`（assistant 主复核，`independent_gold: false`）
  + `DUAL_REVIEW.json`（同模型 deepseek-flash 异构审计 prompt 双复核）。
  Z3 通过不视为语义正确。

## 结果

| 案例 | 工程路由 | 离线 verify | 备注 |
| --- | --- | --- | --- |
| Ekubo | candidate | pass（`prompt_snapshots`） | 公式全过 |
| Hybra | candidate | pass | 公式 P partial（重复谓词，live-4 禁令未防住） |
| Intuition | candidate | pass | live-3 拒绝族成员被交叉相乘处方救回；公式 I partial（弱化为"高于下限"） |
| Merkl | candidate | pass | 公式全过 |
| Panoptic_Hypovault | candidate | pass | 公式全过；1 为文本字面量；3 次调用零修复 |
| Panoptic__Next_Core | candidate | pass | 公式 P/I partial（见拆分） |
| GTE_Perps | rejected | — | 正确拦截：truth 谓词藏界；修复已加源但仍 truth，重试耗尽 |
| SukukFi | rejected | — | 正确拦截（反馈缺口）：两个含数字未选前置被门要求；反馈未点名缺失源 |
| Monetrix | rejected | — | 误伤：`0x811` 槽位常量被计为字面量 2065（族第二例）；修复原样返回 |
| Sequence | rejected | — | 修复纪律失败：`invalid quantity binding` 后原样返回 |

## 准确性拆分

### 要素层（10 例可评）

| 维度 | 通过 |
| --- | --- |
| element P / I / V | 9/10 / 10/10 / 10/10 |
| P 中含后置观察量（捆绑动作+状态） | 1/10（GTE_Perps，干净状态形可提取未选） |

### 公式层（6 例可评）

| 案例 | formula P | formula I | formula V |
| --- | --- | --- | --- |
| Ekubo | pass | pass | pass |
| Hybra | **partial** | pass | pass |
| Intuition | pass | **partial** | pass |
| Merkl | pass | pass | pass |
| Panoptic_Hypovault | pass | pass | pass |
| Panoptic__Next_Core | **partial** | **partial** | pass |

- Hybra P partial：`rhybr_defaults_zero` 与 `gauge_immutable_rhybr` 共用同一
  谓词，不可变性事实失表达（规则给出的出路——移入 assumptions——未被采纳）。
- Intuition I partial：报告主张"应收 100%"，关系只要求
  `received×den > eligible×num`（严格高于下限），高于下限的任何少付都满足 I。
- Panoptic__Next_Core P partial：元组顺序事实被编成 `spot != fast` 的伪造
  不等式（顺序是绑定事实不是值关系）；I partial：错误的轮转绑定被放进
  condition、`blended_tick_correct` 作 relation，使 I 读作"错误绑定下混合
  tick 仍须正确"——在修复后的系统里空洞为真；应要求的恒等绑定从未作为
  relation 出现。

### 拒绝归因（4 例）

| 案例 | 错误链 | 定性 |
| --- | --- | --- |
| GTE_Perps | source missing → 加源但仍 truth → bound hidden | **正确拦截**：忠实形 `total_fee_share == 0` 可表达；单次修复方向正确但未走到 comparison 形 |
| SukukFi | source missing ×2 | **正确拦截（反馈缺口）**：1:1 汇率与 10 上限两个含数字前置未编码；`source missing` 反馈不点名缺失 ID，模型无从修复 |
| Monetrix | literal changed（0x811→2065）→ no change | **误伤**：族第二例；预注册修复方向已应用并离线验证（见结论） |
| Sequence | invalid quantity binding → no change | 修复纪律失败；no-change 处方在预算 1 下机械不可达（见下） |

## live-4 修复点验证状态

| 修复点 | 本批观测 |
| --- | --- |
| 交叉相乘处方（type/unit 反馈） | **生效**：Intuition 由 type/unit 拒绝修复为接受，零派生乘积符号 |
| 重复谓词禁令（自审第 3 条） | **未生效**：Hybra 同形塌缩复现；禁令也够不到已冻结的"报告不拒绝"检查 |
| no-change 专属反馈 | **不可达**：`local repair made no change` 在最后一次尝试的校验中抛出，此时重试已耗尽，反馈永远不会发给模型（Monetrix/Sequence 双确认）。修复需 formal-retries ≥ 2，未预注册，故只披露不改 |
| hex 协议常量误伤（live-3 暂缓项） | 族第二例出现，门槛凑满 → **已按预注册方向修复**（HEX_IDENTIFIER 掩码，bounds 路径不受影响），守护测试 + 离线解锁证明齐备 |

## 工程效率

- 外部调用 40 次；超时 0；JSON 格式失败 0（live-3 为 1）。
- 全量回归失败集 = 已知 10 例基线同集（修复前后各跑一次确认）；live1–4
  全部 17 个候选 run 离线 verify 重放不变。

## 与历史批次的可比性

不可直接比较（各批报告集不相交）。剩余瓶颈序列：

- live3 剩余：(a) type/unit 伪造定义、(b) hex 误伤 n=1、(c) 重复谓词、
  (d) 修复纪律。
- live4 剩余：**(a) 已清零**（type/unit 族无拒绝）；(b) 已修复（预注册）；
  (c) 仍在（prompt 禁令对模型无效，n=1 本批）；(d) 仍在且暴露机械不可达
  缺陷 + 两个"修复方向正确但预算耗尽"案例指向反馈质量（不点名缺失源）。

## 双复核（同模型异构 prompt）

见 `DUAL_REVIEW.json`（deepseek-flash，审计口径 prompt）。结果与主复核的
分歧点将逐条列出。

## 停止规则判定与终局

- live-4 相对 live-3：工程完成率持平（60%），但 (a) live-3 最大拒绝族清零
  且 live-4 修复点一实一虚、(b) 拒绝列迁移（正确拦截 +2、误伤族修复）。
  按约定 live-4 为最后一轮 prompt 迭代，**到此停止**。
- 未预注册的改进项只披露不实施：no-change 反馈可达性（需 retries ≥ 2）、
  `source missing` 反馈点名缺失源、重复谓词的拒绝化（会破坏冻结重放）。
- 下一步：终局保留批 `final_holdout_01`（n=10，冻结于全部迭代之前，从未
  被检视）以最终配置（semantic-live-4 prompt + hex 修复）一次性终测，
  终局报告披露迭代计数（live-1..4 共 4 轮原地修改 + 1 次预注册门修复）。
