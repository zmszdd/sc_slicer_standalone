# final_holdout_02 — 第二终局保留批（semantic-live-5 结构性修改的测量仪器）

冻结于 2026-10-08，在 semantic-live-5 五项结构性修改**任何盲测之前**。零模型
调用，纯选样冻结（`select.py`，盐
`stage2-final-holdout2-2026-10-08-01:`，排除全部 137 个历史 case ID /
139 个报告哈希 / 143 个输入哈希——含 live1–4、final_holdout_01、
accuracy_gold_01 的全部样本；与 final_holdout_01 报告哈希重叠为 0）。

## 这批测什么

final_holdout_01 测的是 live-1..4 迭代环（已收口）。本批只测
**收口后按任务目标补充的 semantic-live-5 五项修改**中两项会改变盲批
指标的行为，外加两项 advisory 的覆盖面收集：

- 门行为变更：`duplicate_predicate_gate`（生成期拒绝重复 P 谓词）
- 放行行为变更：`partial_formalization`（rate 类关系降级为 bool 符号
  + 非阻塞 unsupported_relation）
- 覆盖面收集（不评分）：`requirement_source_review` /
  `intent_scope_review` 两个 sidecar 的标红内容
- 不在本批范围：`stage3-feedback` 闭环（其测量需要阶段三真实代码
  执行，属于阶段三工作，盲批替代不了）

## 预注册判据（跑之前写死，防止事后调参）

| 假设 | 判据 | 判定方式 |
| --- | --- | --- |
| H1 重复谓词门零误伤 | 每个被该门拒绝的 run，其 P 确有同谓词塌缩（拒绝正确）；误伤 > 0 即判门过紧 | 主复核 + 同模型盲双复核 |
| H2 部分形式化忠实 | 走 bool 符号降级的每个候选：符号 meaning 陈述关系本身、source_ids 覆盖关系全部来源、且非"假降级"（本可交叉相乘表达却降级） | 主复核 + 双复核 + `partial-formalization.json` 机械审计 |
| H3 完成率不回退 | 候选 ≥ 6/10（前三批 60% 仅为方向参照，不跨批比较比例） | 机械统计 |

裁判口径与 final_holdout_01 相同：主复核 + 盲双复核（异构审计，
盲于接受状态）；`independent_gold: false` 的根本局限不变，H1/H2 的
置信度受同模型约束。

**判据之外的明确不做**：不做 A/B 双臂（成本翻倍且模型输出非确定、
对照不干净）；不因本批结果再改规则——坏结果以披露形式移交，与
live-4 收口口径一致。本批跑完即停。

## 规则

- **本批永不进迭代**：后续任何 select.py 都会扫描
  `evaluation/**/SELECTION.json` 自动排除这 10 例。
- **跑之前无人看它**：不对这些案例做任何语义检查、probe 或离线试跑。
  （冻结过程只有大小/哈希/项目名的机械筛选。）
- **只跑一次**：`run_terminal.sh` 用当时的 `semantic-live` prompt 跑
  `manifest_a.json` + `manifest_b.json` 两批（batch runner 单 manifest
  上限 5 例），n=10。
- **报告必须披露**：终局报告注明"收口后经 1 轮目标导向结构性修改
  （未预注册于 live 迭代环，事后披露于 STAGE2_CURRENT_STATUS.md）
  测得"，以及本 README 的判据预注册于运行之前。

## 已知口径细节（如实披露）

- 池中同一项目存在多份不同报告实例；排除是机械三重排除
  （case ID / 报告哈希 / 输入哈希），不是语义去重——项目名可能
  与历史批重复（SukukFi/GTE/Hybra 等在 live-4 与 final_holdout_01
  已有此先例）。判读 H1/H2 时按"报告实例未见"计，不按"项目未见"。
- `--formal-retries 1` 的 no-change 反馈不可达缺陷随 live-4 披露
  继承，未在本轮修改。
- 双复核裁判为 deepseek-flash 同模型（与终局批相同的根本局限）。

## 运行（已于 2026-10-08 经用户授权执行一次）

```bash
bash run_terminal.sh
```

实际执行：生成 36 次调用 + 双复核 10 次 = 46 次，当日跑完。
结果见 [REPORT.md](REPORT.md)（三假设逐条判定 + 全部 run 离线
verify + 误伤/假降级逐例归因）。本批已消耗，不再重跑。

## 追记（2026-10-09，事后离线诊断，未重跑本批）

5 例失败的离线重放定位（零模型调用；冻结 run 未动）：

| 案例 | 记录错误 | 离线重放根因 | 归类 |
| --- | --- | --- | --- |
| Covenant | invalid quantity binding | conservation 的 before/after 槽要求数量表达式，模型塞了比较谓词（该用 correspondence）；重试 hint 只讲 QEXPR 形状 | hint 缺模板指引 |
| GTE_Perps | local repair made no change | 数值 gate 不把 "greater than zero" 的 zero 识别为常量 0，反而强索括号里的 1e16；模型忠实拒绝改，被判"无修改" | **gate bug（已修）** |
| Kinetiq | numeric P source missing | 第 1 次重试已修好 self-comparison，暴露带指针的新错误，但预算只剩 1 次重试 | 重试预算不足 |
| Monetrix | P symbol not grounded | 两轮各修一处又暴露下一处，未在 1 次重试内收敛 | 重试预算不足 |
| Olas | trivial self-comparison | 修复压力下退化出 x==x | 重试退化 |

处置（面向 final_holdout_03，本批已消耗不重跑）：

1. **gate 修复**：`explicit_numbers` 把比较语境中的 "zero" 识别为常量 0
   （"greater than zero" 接地 const 0）；修辞用法（"effectively zero"）与
   地址哨兵（"zero address"/`address(0)`，后者旧版还会把括号里的 0 当
   数字——live-4 Hybra 同源误报）不触发。63 个已接受 plan 全量扫描：
   仅 2 个行为差且均为期望方向（Hybra 误报消除；archive v320 SukukFi
   "returns zero" 真漏编码被正确拦截）。
2. **hint 增强**：'invalid quantity binding' 反馈补充 conservation/
   correspondence 模板区分；'numeric P literal changed' 反馈补充
   "两数量比较用符号对符号，文本没有的常量即使语义等价也算发明"
   （GTE_Perps 第二拦截点：模型以 accrued_fee>0 编码"余额超过储备"）。
3. **重试预算**：final_holdout_03 建议以 `--formal-retries 2` 运行
   （CLI 已支持；Kinetiq/Monetrix 类一轮修不完的结构错误需要第二次
   重试，成本 +1 模型调用/失败案例）。
