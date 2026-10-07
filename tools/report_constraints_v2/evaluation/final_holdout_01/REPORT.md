# 终局保留批终测（final_holdout_01，n=10）

## 迭代披露（按保留批 README 约定）

- 本批 10 例于 **2026-10-06 冻结**（早于 live-3/live-4 两轮迭代），冻结后至
  本次终测前从未被检视；全部历史选择脚本经 SELECTION.json 扫描自动排除
  本批，四轮盲批（live-1..4）与此批样本不相交。
- 终测前 prompt 共 **4 轮原地迭代**（semantic-live-1..4，2026-10-06..07）
  外加 **1 次预注册门修复**（hex 字面量扫描，方向与 ≥2 例触发条件均在
  live-3 报告中预注册，于 live-4 后应用）。停止规则（live-2 后最多再
  2 轮）被遵守：live-4 为最后一轮。
- 终测配置与盲批完全一致（`--formal-retries 1` 等；no-change 反馈在该
  预算下不可达的缺陷已在 live-4 报告披露，未做未预注册的改动）。

## 结论

- **工程完成 8/10 候选**（live1 60%、live2 60%、live3 60%、live4 60% →
  终局 80%），八例全部通过零模型调用的离线 verify；32 次外部调用、
  超时 0、JSON 失败 0、要素层弃权 0。
- **两例拒绝均为 Z3 一致性正确拦截**（数值门拒绝 0、误伤 0）：
  - Merkl：P 把违约后果本身钉死（liabilities 2000 > physical 1990 全在
    P），P∧I 不可满足——过度具体化被一致性层拦下，未作为产物放出。
  - Panoptic__Next_Core：P 并置互斥分支（position_in_range 同时为真为假），
    P 自身不可满足——被拦下。
- **忠实结果口径**：公式层严格全过 6/8；+2 例一致性正确拦截 = **8/10
  忠实结果**；2 例可见缺陷以候选形式通过（GTE_Perps 重复谓词塌缩、
  SukukFi 文档要求混入 P），均被 report-only 检查与双复核暴露、未被
  静默当作真。
- **双复核（同模型异构 prompt，n=10）与主复核在核心缺陷形态上收敛**：
  GTE_Perps 与 Panoptic__Next_Core 的谓词塌缩被两边独立抓到；双复核对
  适用范围收窄（Intuition/Olas/SukukFi）系统性更严（评 partial），主复
  核以 unresolved/limitations 已披露为通过。两套复核均无 fail 评级。

## 结果

| 案例 | 工程路由 | 离线 verify | 公式 P / I / V | 备注 |
| --- | --- | --- | --- | --- |
| Covenant | candidate | pass | pass / pass / pass | 时序有效性；缺数值定义如实入 unresolved |
| GTE_Perps | candidate | pass | **partial** / pass / pass | 重复谓词（两源共用 pair_already_exists） |
| GTE_Spot | candidate | pass | pass / pass / pass | 界常量 15/16 均文本字面量 |
| Hybra | candidate | pass | pass / pass / pass | live-1/3 伪造定义族零复发 |
| Intuition | candidate | pass | pass / pass / pass | 份额级公平关系；符号化无数值定义如实披露 |
| Olas | candidate | pass | pass / pass / pass | elapsed>0 字面量 0；滑点界为自由布尔 |
| Sequence | candidate | pass | pass / pass / pass | live-4 的 no-change 拒绝未复发 |
| SukukFi | candidate | pass | **partial** / pass / pass | 文档要求混入 P（要素+公式层） |
| Merkl | 一致性拒绝 | — | P fail（钉死违约后果） | 正确拦截 |
| Panoptic__Next_Core | 一致性拒绝 | — | P fail（互斥分支并置） | 正确拦截 |

## 准确性拆分

| 层 | 结果 |
| --- | --- |
| 输入筛查 | 10/10 就绪，0 弃权 |
| 要素层 P / I / V | 9/10 / 10/10 / 10/10（SukukFi 文档要求混入 P） |
| 公式层（8 例可评）P / I / V | 6/8 / 8/8 / 8/8 |
| 拒绝归因 | 2 一致性正确拦截，0 误伤，0 数值门拒绝 |
| 忠实结果 | 严格 6/10；含正确拦截 8/10 |

## 复核方法与局限

- 主复核（SEMANTIC_REVIEW.json）：assistant 依据冻结报告输入、要素、形
  式计划与确定性 AST 逐例评级；`independent_gold: false`——没有独立人工
  金标准，这是本测量的根本局限。
- 双复核（DUAL_REVIEW.json）：deepseek-flash 异构审计 prompt（与生成
  prompt 结构不同、评级语言独立），每例一次调用。分歧点（双复核更严的
  范围收窄判定）逐例记录于两份 JSON，未强行归一。
- Z3 一致性通过不视为语义正确；所有"通过"仅指翻译忠实性判断。

## 终局判定

阶段二目标口径（"未见报告的漏洞主张无损翻译为机器可检查的形式化声明，
翻译本身可验证"）下的最终状态：

1. **翻译可验证性**：全部产物可零模型调用离线重放（prompt 快照 + 代码
   哈希）；17+10=27 个候选 run 的重放在 hex 修复前后均不变。
2. **忠实性**：终局批 8/10 忠实结果（6 严格 + 2 正确拦截）；两个漏网
   缺陷均为"可见不拒绝"型（report-only 检查暴露），无一被静默当真。
3. **零人工**：全程 deepseek-flash 单模型，选择冻结、运行、复核、报告
   均无人工介入（用户仅授权运行）。
4. **诚实边界**：无独立金标准；prompt 经 4 轮盲测迭代（已披露）；剩余
   已知缺陷族（重复谓词、文档要求混入 P、no-change 反馈不可达）以披露
   形式移交，不做第四轮以后的迭代。

阶段二到此收口。
