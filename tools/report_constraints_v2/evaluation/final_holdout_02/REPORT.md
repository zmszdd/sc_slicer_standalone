# 第二终局保留批终测（final_holdout_02，n=10）——semantic-live-5 结构性修改测量

## 披露（按本批 README 预注册约定）

- 本批 10 例于 **2026-10-08 冻结**（三重排除 137 case ID / 139 报告哈希 /
  143 输入哈希，含 live1–4、final_holdout_01、accuracy_gold_01 全部样本；
  与 final_holdout_01 报告哈希重叠 0），冻结后至终测前从未被检视。
- 本批测的是 **收口后 1 轮目标导向结构性修改**（semantic-live-5，2026-10-08，
  未预注册于 live 迭代环，事后披露于 STAGE2_CURRENT_STATUS.md）。判据
  H1/H2/H3 预注册于运行之前的本目录 README。
- 终测配置与历史盲批一致（`--formal-retries 1`；no-change 反馈与
  source-missing 反馈的两个已披露缺陷随 live-4 继承，未做未预注册改动）。
- 排除是机械三重排除，非语义去重：项目名可与历史批重复（本批
  SukukFi/Panoptic Next Core/GTE×2/Intuition/Covenant/Hybra/Monetrix/Olas/
  Kinetiq 均为同项目的**不同报告实例**）。

## 结论

- **工程完成 5/10 候选**（final_holdout_01 终局为 8/10；两批样本不同、
  报告难度不同，比例不可直接比较——本批含多份长报告与数值密集型 PoC）。
  五例候选全部通过零模型调用离线 verify；36 次生成调用、超时 0、
  JSON 失败 0、要素层弃权 0。
- **五例拒绝全部为正确拦截（误伤 0）**：无一例是机械规则误伤忠实计划——
  每例的最后一次计划尝试都带有真实缺陷（退化谓词、模板形状错误、
  数值字面量替换、定义混入 P、数值来源丢失），被既有 schema/数值/接地
  门拦下。Z3 一致性拦截 0 例（缺陷计划全部在更早的门被拦下）。
- **H1（重复谓词门零误伤）：满足**——门零触发、零误伤，且五候选中
  也不存在漏网的重复谓词塌缩。但门的必要性在本批未得到演示（模型
  未产生塌缩尝试）。
- **H2（部分形式化忠实）：空转满足**——部分形式化通道零使用：无候选
  降级，无拒绝属于 blocking unsupported_relation 族。通道未证明收益
  也未产生误用；其价值要等 DSL 表达力不足的场景出现（或阶段三绑定）。
- **H3（完成率 ≥ 6/10）：不满足**——5/10。但五例拒绝全部为正确拦截，
  缺口在模型缺陷侧而非误拒侧：按忠实口径 9/10（4 严格 + 5 正确拦截）。
- **一个漏网候选缺陷（可见、披露、未被机械拦截）**：Hybra 的交叉相乘
  配对歧义——`shares*A_before ≥ deposit*S_after`。配对仅在
  `total_shares_after` 被读作"铸造前供给"（= S_before）时恰为报告的
  公平式 `shares*A_before ≥ deposit*S_before`；按符号声明的"铸造后
  总量"读法，不变量变为 `shares*(A-deposit) ≥ deposit*S`，用报告自己
  的数字，**公平实现也会违反**（5000×10000 < 5000×15000）——阶段三
  绑定会产生假违规。关系式与符号声明二者必有一错；主复核与双复核
  独立均判 I partial（双复核抓到的是同一计划上的示例值钉死，未察觉
  配对歧义）。另有 P 过定（示例常量钉死）与 V 单主张压缩（均如实
  披露）。这是本批唯一非严格通过的候选。
- 两 advisory（requirement-source / intent-scope）在五候选上零标红，
  无假阳性；亦未捕获 Hybra 缺陷（其收窄是数值过定，不是 impact 接地）。

## 结果

| 案例 | 工程路由 | 离线 verify | 公式 P / I / V | 备注 |
| --- | --- | --- | --- | --- |
| SukukFi | candidate | pass | pass / pass / pass | KYC 绕过；收窄如实披露 |
| Panoptic Next Core | candidate | pass | pass / pass / pass | init 无访问控制 |
| GTE_Spot | candidate | pass | pass / pass / pass | ZeroCostTrade 误伤 |
| Intuition | candidate | pass | pass / pass / pass | 纪元超发；PoC 数字未混入 P |
| Hybra | candidate | pass | **partial** / **partial** / **partial** | 交叉相乘配对歧义 + 示例值钉死 |
| Olas | 拒绝 | — | — | 退化 x==x 谓词（正确拦截） |
| Covenant | 拒绝 | — | — | conservation 模板形状错误（正确拦截） |
| GTE_Perps | 拒绝 | — | — | 数值字面量替换 + no-change 修复失败（正确拦截） |
| Monetrix | 拒绝 | — | — | 定义混入 P + 未接地符号（正确拦截） |
| Kinetiq | 拒绝 | — | — | 数值来源字面量丢失（正确拦截） |

## 准确性拆分

| 层 | 结果 |
| --- | --- |
| 输入筛查 | 10/10 就绪，0 弃权 |
| 要素层 P / I / V | 9/10 / 10/10 / 10/10（Olas 代码行为事实被硬塞进 P 谓词） |
| 公式层（5 例可评）P / I / V | 4/5 / 4/5 / 4/5 |
| 拒绝归因 | 5 正确拦截，0 误伤，0 Z3 一致性拦截 |
| 忠实结果 | 严格 4/10；含正确拦截 **9/10** |
| 新功能 | 重复谓词门 0 触发 0 误伤；部分形式化通道 0 使用；advisory 0 标红 0 假阳性 |

## 预注册判据判定

| 假设 | 判定 | 依据 |
| --- | --- | --- |
| H1 门零误伤 | **满足** | 门零触发；候选无塌缩漏网；无任何因门拒绝的 run |
| H2 降级忠实 | **空转满足** | 通道零使用——无降级事件可评 |
| H3 完成率 ≥6/10 | **不满足** | 5/10；但拒绝侧全为正确拦截，缺口在缺陷侧 |

## 复核方法与局限

- 主复核（SEMANTIC_REVIEW.json）：assistant 依据冻结报告输入、要素、
  形式计划/最后一次尝试与确定性拒绝消息逐例评级并给出拒绝对抗式
  归因；`independent_gold: false`——没有独立人工金标准，是本测量的
  根本局限。
- 双复核（DUAL_REVIEW.json）：deepseek-flash 异构审计 prompt（与
  final_holdout_01 同一 prompt、同一评级语言），每例一次调用，
  盲于接受状态。结果见下节。
- Z3 一致性通过不视为语义正确；所有"通过"仅指翻译忠实性判断。
- 模型总调用：生成 36 + 双复核 10 = 46 次（终局批口径为 32 + 复核）。

## 双复核结果（DUAL_REVIEW.json，deepseek-flash 异构审计，10 次调用）

| 案例 | 双复核 formal P / I / V | 主复核 formal P / I / V | 收敛性 |
| --- | --- | --- | --- |
| GTE_Spot | pass / pass / pass | pass / pass / pass | 完全收敛 |
| Hybra | pass / **partial** / partial | partial / **partial** / partial | 缺陷存在性收敛（I 均非 pass）；双复核抓示例值钉死，未察觉配对歧义 |
| Intuition | pass / **partial** / partial | pass / pass / pass | 分歧：双复核更严（适用范围收窄 + reclaim 影响推迟） |
| Panoptic | pass / **partial** / partial | pass / pass / pass | 分歧：双复核更严（收窄到具体攻击者配置 + 费用抽取影响推迟） |
| SukukFi | **partial** / **partial** / pass | pass / pass / pass | 分歧：双复核更严（收窄到 validator 调用者子例） |
| 5 例拒绝 | 全 not_evaluable | — | 双复核确认要素层忠实、无形式产物可评 |

- **与 final_holdout_01 相同的收敛模式**：核心缺陷形态（Hybra 非严格）
  被两套复核独立抓到；分歧集中于适用范围收窄的严格度（双复核系统性
  更严），主复核以 unresolved/limitations 已披露为通过（单主张压缩为
  设计取舍）。**无任何案例在两套口径下互换通过/拒绝**。
- 双复核对五例拒绝均确认"要素层无实质缺陷"——与主复核的拒绝归因
  （全部为公式层/机械层缺陷被正确拦截）一致。
- 如实披露：双复核没有独立验证主复核发现的 Hybra 配对歧义（判
  partial 的理由是另一处缺陷）；该歧义的数学推导只记录在
  SEMANTIC_REVIEW.json，未经第二双复核确认。
- 模型总调用：生成 36 + 双复核 10 = **46 次**（超时 0、JSON 失败 0）。
