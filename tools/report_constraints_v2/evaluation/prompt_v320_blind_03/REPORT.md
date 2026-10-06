# semantic-v3.20 新报告盲测（5 例）

## 结论

这次使用了 5 份未出现在历史评测记录中的 `exact_submission` 报告。样本在模型调用前按固定
哈希规则冻结，没有根据运行结果挑样。

- 输入充分性：**5/5**；
- 要素 schema/证据校验：**5/5**；
- 完整生成公式并通过程序检查：**4/5（80%）**；
- 4 个候选零模型离线重放：**4/4**；
- 要素层严格 P/I/V 全忠实：**2/5（40%）**；
- 最终公式层严格 P/I/V 全忠实：**0/4**。

因此，`semantic-v3.20` 当前可以作为**候选生成与辅助审核工具**，但不能无人工复核地作为
最终规则生成器。最明显的优势是 I 与 V 的自然语言方向较稳定；最主要的缺陷是 P 的时间角色、
关键触发条件完整性，以及这些错误向 I 的适用条件传播。

上述语义数字来自助手对报告和产物的逐例复核，不是专家金标准；`n=5` 也不能外推为总体准确率。

## 样本和规程

- 来源：`verified_flatten_pass_1568_exact_cases`；
- 排除：历史 evaluation/results JSON 中出现过的 83 个案例；
- 候选条件：`exact_submission`、报告正文不少于 500 字符；
- 排序：`sha256("stage2-v320-blind-02:" + case_id)` 升序取前 5；
- 模型：`deepseek-flash`；Prompt：`semantic-v3.20`；
- 参数：要素重试 1 次、形式计划重试 1 次、lean formal input、signals verdict；
- 评价：工程完成率与语义忠实度分别统计，Z3 通过不计作语义正确。

冻结选择及输入哈希见 `SELECTION.json`。

## 结果

| 案例 | 工程结果 | 要素 P/I/V | 公式 P/I/V | 主要问题 |
| --- | --- | --- | --- | --- |
| Olas TWAP | candidate | pass/pass/pass | pass/partial/pass | I 丢失“偏差超过 slippage”这一数值适用条件；关系分类不当 |
| Hybra emissions | candidate | fail/pass/pass | fail/partial/pass | `_ratio=0`、`claimable` 不变被错误放入执行前 P |
| GTE Spot bitwise | failure | pass/pass/pass | —/—/— | 修复后的布尔表达忠实，但被 numeric guard 误拒绝 |
| GTE graduation | candidate | fail/pass/pass | fail/partial/pass | P 未形式化“攻击者先创建同一 pair”这一关键触发事实 |
| Panoptic BuilderWallet | candidate | partial/pass/pass | fail/partial/pass | 未建立 unauthorized caller 与既有合法 admin 的关系 |

## 准确性拆分

### 要素层

| 维度 | 严格通过 |
| --- | ---: |
| P | 2/5 = **40%** |
| I | 5/5 = **100%** |
| V | 5/5 = **100%** |
| P/I/V 同时通过 | 2/5 = **40%** |

### 最终公式层

只在 4 个成功产出公式的案例上计算：

| 维度 | 严格通过 |
| --- | ---: |
| P | 1/4 = **25%** |
| I | 0/4 = **0%**（4 例均为方向正确但条件不完整/被污染） |
| V | 4/4 = **100%** |
| P/I/V 同时通过 | 0/4 = **0%** |

这里的“严格”要求条件、时间角色和作用域均忠于报告。I 的 0% 不表示安全方向全部反了，
而是四个 I 都存在重要的适用条件损失：数值界限被布尔化、后置结果混入条件、攻击排序遗漏，
或授权主体没有建模。

## 工程效率

- 模型调用：16 次；
- 模型累计耗时：54.409 秒；
- Token：58,763（输入 44,967，输出 13,796）；
- 单案例平均：3.2 次调用、约 11,753 tokens；
- 完成候选：4/5。

批处理包装器首次使用相对输出路径时暴露路径解析 Bug：子进程改变工作目录后把产物写到嵌套路径，
父进程随后找不到 `pipeline-stdout.txt`。5 个子任务本身均已完成，产物原样迁移到本目录，未重新
调用模型。该问题不计入 Prompt 成绩。

## 下一步

1. 在 P 校验中明确区分“执行前事实”和“动作后派生结果”，禁止 `claimable unchanged` 一类
   后置观察量进入 P；
2. 要求形式计划覆盖报告中的关键攻击动作/排序，例如 `pair already exists because attacker mined first`；
3. I 的适用条件必须保留报告中的数值界限或授权主体，不能只用宽泛 Boolean 代替；
4. 调整 numeric guard：允许无法由当前 DSL 表达的位运算关系作为显式、有证据的 Boolean，避免
   GTE Spot 这种语义正确候选被机械误拒绝；
5. 批处理相对输出路径已在本次测量后修复；后续应使用修复后的入口在另一批新报告上复验，
   不能用本批样例继续调分后再报告盲测成绩。
