# 阶段二准确率测评（同模型两阶段盲金裁判，全部 40 例冻结 run）

## 结论

- **翻译保真的核心指标干净**：150 个维度评级（25 候选 × 6 维度）中
  **unfaithful 仅 3 例，且全部集中在 I（required_property）维度**；P 与 V
  维度（element + formula 共 100 个评级）unfaithful 为 **0**。逐条裁决后：
  3 例中 2 例（live2 Intuition）被报告原文直接证据推翻为争议判读，
  1 例（live4 Panoptic 公式 I 循环编码）为真实缺陷但已被主复核与双复核
  同步抓到——**金裁判未发现任何两套既有复核之外的新的失真翻译**。
- **"weakened"大量出现是设计内的单主张压缩，不是失真**：V 维度 21–22/25
  为 weakened，源于每例只形式化报告的一条核心主张（其余 impact 记入
  limitations 推迟）——这是阶段二"一报告一可检主张"的设计取舍，裁判以
  "全报告覆盖"口径评 weakened。I 维度的 weakened（15–16/25）主要是
  叙事性 qualifier 的符号化压缩。
- **多层系统准确率**（40 例口径）：
  - 严格（六维全 faithful + 拒绝全正确）：**12%**——此口径把单主张压缩
    全数计为不满，不适合作为阶段二目标函数。
  - 忠实（无任何 unfaithful + 拒绝正确）：**70%**。
- **金裁判在机械拒绝层不可靠**：对 15 例拒绝给出 10 misfire / 4 correct
  catch / 1 honest abstain，与主复核归因（约 10 正确拦截 + 2 误伤 + 
  1 诚实弃权 + 2 修复纪律失败）大面积冲突。两条硬证据：终局批 Panoptic
  的 P 自相矛盾（Z3 一致性拦截，P∧V 不可满足）被裁判漏判为 misfire；
  同一 `0x811` hex 误伤族（live3 与 live4 的 Monetrix 同族同形）被判成
  两个相反的 verdict（misfire vs correct_catch）。
- **主复核校验**：金裁判与主复核公式层评级一致 24/54，全部分歧方向为
  主复核 pass vs 金 weakened（主复核以"收窄已记录于 unresolved/limitations
  为通过口径"）——分歧是口径差，无任何案例在两套口径下互换通过/拒绝，
  与双复核的结论同构。

## 测评设计和规程

- 范围：全部 5 个已冻结批次（live1–live4 盲测 + 终局保留批）共 40 个 run
  （25 候选 + 15 拒绝），产物零改动、纯事后测评。
- 金标准提供者：**deepseek-flash 两阶段盲裁判**（受"全程同一模型"约束，
  无异构模型可用）。设计（`gold_review.py`）：
  - **Phase 1（shadow）**：裁判只看报告原文，用自己的话重述核心主张
    （before/required_property/bad_outcome）——重述不可能被机器产物锚定。
  - **Phase 2（compare）**：裁判看报告 + 自己的重述 + 机器产物（候选：
    elements + formal plan；拒绝：最后一次形式化尝试 + 拒绝错误），以
    faithful/weakened/unfaithful 评 6 个维度。全程盲于流水线接受状态、
    主复核、双复核。
- 80 次外部调用（40 案例 × 2 阶段），超时 0、JSON 失败 0。
- 已披露局限：同模型自偏好（裁判与生成器同为 deepseek-flash）。两阶段
  shadow 设计与盲载荷是缓解手段；结果是**同模型盲金测评**，不是人类金
  标准。事后逐条裁决（下文）是对该偏差的补救。

## 翻译准确率拆分（25 候选）

| 维度 | faithful | weakened | unfaithful |
| --- | --- | --- | --- |
| element P | 13 | 12 | 0 |
| element I | 8 | 16 | 1 |
| element V | 4 | 21 | 0 |
| formula P | 13 | 12 | 0 |
| formula I | 8 | 15 | 2 |
| formula V | 3 | 22 | 0 |

- 严格六维全过 0/25；无 unfaithful 23/25（仅 live2 Intuition 与 live4
  Panoptic 两例有 unfaithful 评级）。
- 裁判的独立机械检查与已知缺陷族**完全收敛、零新发现**：
  `constants_not_in_report` 0 条（与数值门守门结果一致）；`collapsed_facts`
  6 条全部命中已记录的重复谓词塌缩族（live3 两个 Panoptic、live4 Hybra、
  终局 GTE×2、SukukFi）。

### 三个 unfaithful 评级的逐条裁决

1. **live2 Intuition（element I + formula I，2 评级）——争议判读，不成立
   为确认失真**。裁判称报告要求"validity window 密码学绑定进签名"，而
   机器只编码了"窗口强制"。逐条核对（本报告写作时完成的裁决）：
   - 报告原文明句："The EntryPoint is then expected to enforce that the
     operation only executes within that window."——机器的 relation
     （valid_after ≤ execution_time ≤ valid_until）正是这句的字面编码；
   - 绑定缺陷**并未缺席**：计划的 I 适用条件显式包含
     `suffix_in_digest = false`（validity 字节不在签名摘要内）与
     `attacker_can_intercept = true`，整条读作"当窗口未被绑进摘要且攻击
     者可拦截时，执行仍须落在声明窗口内"——即报告描述的失效模式本身；
   - 裁判孤立地读了 relation、漏读 condition 携带的绑定状态，并把
     "应有属性"读成比报告文本更强的绑定主张。两种读法都可辩，机器选的
     是有报告原句支撑的那种。**记为报告歧义暴露，非失真**。
2. **live4 Panoptic（formula I）——真实缺陷，但非新发现**：错误的轮转
   绑定放进 condition、`blended_tick_correct` 作 relation，I 在修复后的
   系统里空洞为真（循环编码）。主复核（partial）与双复核均已同形抓到，
   金裁判与其收敛。

## 拒绝归因对照（15 例，金裁判 vs 主复核）

| 维度 | 金裁判 | 主复核 |
| --- | --- | --- |
| misfire | 10 | 2（两个 Monetrix hex，预注册修复已应用） |
| correct_catch | 4 | ~10 |
| honest_abstain | 1 | 1（Kinetiq 输入筛查弃权，两者一致） |
| 修复纪律失败 | （归入 misfire） | 2 |

裁判机械层不可靠的两条硬证据（结论一节已列）：终局 Panoptic 的 P
自相矛盾被漏判 misfire；同一 hex 族两批两个相反 verdict。其余冲突的
共同机制：裁判只评估"最后一次尝试是否忠实/显然可修"，不进入
求解器一致性（P∧I unsat / P∧V 不可满足）、数值门纪律（藏界、伪造
定义）与冻结重试预算的语境——而这些正是拒绝存在的原因。两个领域
裁判与主复核一致：输入筛查诚实弃权（Kinetiq）、live1 的数值门
assumption 误伤（live-2 已修复并验证生效的族）。

**采纳的结论**：翻译保真采信金裁判（经逐条裁决修正）；拒绝归因不采信
金裁判，维持主复核 + 双复核口径。

## 系统准确率（多层）

| 口径 | 数值 | 说明 |
| --- | --- | --- |
| 严格（六维全 faithful + 拒绝全对） | 12% (0+5)/40 | 单主张压缩使六维全过为 0；非目标函数 |
| 忠实（无 unfaithful + 拒绝全对） | 70% (23+5)/40 | 采信翻译层、不采信机械拒绝层后的口径为 **23/25 + 主复核拒绝归因** |
| 工程完成率（既有口径） | 25/40 = 62.5% | 含 2 例 Z3 一致性正确拦截的终局 8/10 |

按采信口径重述：**25 个候选中 24 个无失真翻译评级（96%），其中 2 个
存在已被双复核收敛确认的 I 维度真实弱化/循环缺陷；15 个拒绝中 12 个
为主复核口径的正确拦截/诚实弃权**。

## 金 vs 主复核一致性

公式层三维度 54 个可比评级一致 24/54；30 个分歧**全部**是主复核
pass vs 金 weakened（无反向、无 fail 级分歧、无通过/拒绝互换）。与双
复核的分歧结构相同：裁判口径把"收窄已如实记录于 unresolved/
limitations"计 weakened，主复核以记录为通过。主复核的宽松是有记录
的口径选择而非漏检——金裁判的独立机械检查（上节）未发现主复核
漏掉的任何机器缺陷。

## 局限

- 同模型自偏好：金标准由与生成器相同的 deepseek-flash 提供（全程
  同模型约束所致），偏差方向理论上偏向宽松，但本测评的翻译层结果
  经逐条裁决以报告原文为准修正，不依赖裁判善意。
- 机械拒绝层不可采信（如上），系统准确率中"拒绝全对"部分使用主复核
  口径补足。
- 事后测评：裁判所见冻结产物与既有复核所见完全相同，无新信息注入
  翻译层（其价值在于独立口径与 shadow 重述）。
- 单主张设计使"全报告覆盖"类 weakened 不可比：阶段二目标是一报告
  一可检主张，非覆盖率。

## 产物

- `gold_review.py`（两阶段协议 + 载荷构造）、`analyze.py`（指标）。
- `gold-review/<batch>__<case>/{shadow,judge}/`：每例两阶段的完整调用
  载荷与原始回复。
- `GOLD_REVIEW.json`（schema stage2-accuracy-gold-review/1，40 案例）、
  `METRICS.json`（schema stage2-accuracy-metrics/1）。
