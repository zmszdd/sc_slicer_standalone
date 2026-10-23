# 当前 semantic-live 忠实度测量（n=5）

日期：2026-10-20。目的：在不改动 Prompt、规则或修复代码的前提下，测量当前 `semantic-live` 的报告翻译忠实度，并定位下一步可改善处。本批是一次测量，不作为下一轮调参开发集。

## 方法

- 在模型调用前冻结 5 份未见报告。按 case ID、报告 SHA-256、提取输入 SHA-256 三重排除历史样本；来自 5 个不同项目。冻结记录、逐例哈希、Prompt 哈希和代码哈希见 [SELECTION.json](SELECTION.json)。
- 选择脚本复制自 live4 评测模板；运行后发现并更正了 `SELECTION.json` 中沿用的旧 `purpose` 描述。更正只涉及说明文字，案例清单、报告/输入哈希、Prompt 哈希和代码哈希均未变，详情见该文件的 `metadata_note`。
- 当前工作树配置：DeepSeek `deepseek-flash`、`semantic-live`、report-json-input/4、精简形式化输入、提取与形式化各最多一次重试、`--continue-on-review`。本批不提供参考答案。
- 生成后先运行两阶段盲评：评审先只读报告写独立 P/I/V 摘要，再对照系统输出评分；之后使用不同格式的第二个评审 Prompt 复核。两位评审都使用 DeepSeek `deepseek-flash`，不构成人工或独立专家金标准。
- 实际生成调用 21 次，评审调用 15 次，共 36 次。外部模型生成的原始产物保存在 `runs/`、`gold-review/` 和 `dual-review/`。
- 4 个候选均通过零模型调用 `verify`；逐例结果保存在 [VERIFY.json](VERIFY.json)。拒绝案例没有完整形式化产物，不适用候选重放。

## 结果

| 案例 | 路由 | 两阶段盲评 | 主要发现 |
| --- | --- | --- | --- |
| Covenant | rejected | **误拒 / misfire** | 报告给出 `marketBaseTokenSupply <= 2^noCapLimit` 且 `noCapLimit = 60`；计划仍用 `power_of_two(60)` 表达，数值门把它判成引入 `2^60` 常量。异构复核确认报告要素忠实，形式阶段因而不可评分。 |
| GTE Perps | candidate | weakened | I `reward_recipient == staking_user` 忠实；V 只表达收款人不符，没有形式化奖励永久锁定及用户损失。 |
| GTE Spot | candidate | weakened | 公式用“此前订单仍可达”的布尔量表示列表性质，没有直接表达 `prevOrderId` 写入存储；锁定抵押品影响未形式化。 |
| Hybra | candidate | weakened | 前提忠实；I 只表达子 NFT 金额守恒，没有覆盖 `permanentLockBalance` 对账；V 只表达舍入损失。 |
| Panoptic | candidate | weakened（评审有分歧） | 核心条件、`_move=false` 和错误 token delta 对齐。次级池失衡和清算回退标为 deferred；两阶段盲评因此降级，异构复核认为直接核心 claim 已完整。 |

两阶段盲评对 4 个候选的公式 P/I/V 评分分别为：P `2 pass / 2 partial`，I `2 pass / 2 partial`，V `0 pass / 4 partial`；4/4 总评为 `weakened`，没有判为 `unfaithful`。拒绝案例被评为一次误拒。异构复核也认为 3/4 个候选的 V 有实质弱化；Panoptic 是否应因明确 deferred 的下游影响而降级存在分歧。

因此不能把“4/5 严格忠实率”或“0/4”当成稳定准确率：样本仅 5 例、评审均为同一模型，且评分把**选定核心 claim 的正确性**与**整份报告的影响覆盖率**部分混在一起。更稳妥的描述是：4 份候选均保留正确方向，但本批没有一份在两阶段盲评的全报告口径下达到完全无损；1 份有明确的机械误拒风险。

## 分开计分：核心 claim 与影响覆盖

为避免“核心公式对，但其他影响 deferred”与“核心公式本身有偏差”共用一个 `weakened` 标签，本报告对现有评审理由做了**范围调整后的回溯重编码**：

- 核心 P/I/V 只按系统实际选中的一个 claim 评分；其余影响不再扣核心分。
- 影响覆盖逐条比较报告的直接影响与规格：`full`、`partial`、`deferred`、`not_extracted`。被拒绝且没有正式规格的报告单独记为 `not_formalized_rejected`。影响分母取报告侧 phase-1 shadow 和复核理由列出的直接结果，不只取系统抽出的 impact 列表，以免漏掉提取阶段漏报的影响。
- 这不是新盲评：重编码依据现有两份评审的理由，由本报告作者事后按上述口径归类；评审仍来自同一个模型。因此结果用于诊断评分混杂，不作为独立金标准或新准确率估计。

### 核心 claim P/I/V

| 候选 | P | I | V | 核心 claim 结论 |
| --- | --- | --- | --- | --- |
| GTE Perps | partial | faithful | partial | 缺少 Launchpad caller/no-forwarding 前提；V 只写 recipient 不等于 user，没有明确落到 Launchpad。 |
| GTE Spot | partial | partial | faithful | P 漏掉存储 `prevOrderId=0` 和仅更新 memory copy；I 用可达性布尔量代替存储链接关系。 |
| Hybra | faithful | partial | partial | I 漏掉永久余额核算；V 的守恒违例没有限定为报告中的 `child sum < parent` 损失方向。 |
| Panoptic | faithful | faithful | faithful | 所选直接影响的前提、关闭语义和错误 token delta 均对齐。 |

4 个候选中，P 为 **2 faithful / 2 partial**，I 为 **2 / 2**，V 为 **2 / 2**；核心 P/I/V 全部 faithful 的是 **1/4**（Panoptic）。Covenant 因未生成正式规格，不纳入公式核心维度分母。

### 直接影响覆盖

| 案例 | 每项影响状态 |
| --- | --- |
| Covenant（rejected） | `large_growth_bypass`、`subsequent_mints_revert`、`deposit_dos`：均 `not_formalized_rejected` |
| GTE Perps | `rewards_sent_to_launchpad`：partial；`rewards_locked`、`users_lose_rewards`：deferred |
| GTE Spot | `earlier_orders_orphaned`：full；`collateral_locked`：deferred；open-interest inflation、limited tree-node consumption：not_extracted |
| Hybra | `rounding_loss`：partial；`balance_exceeds_true_total`：deferred |
| Panoptic | `incorrect_token_deltas`：full；`pool_imbalance`、`liquidation_revert`：deferred |

4 个候选对应的 12 项报告侧直接影响中，**2 full、2 partial、6 deferred、2 not extracted**；Covenant 另有 3 项因拒绝而没有正式表达。这样可以分别看出：Panoptic 的核心 claim 完整，但整份报告仍只覆盖一个影响；GTE Spot 的所选核心影响已表达，列表存储关系的精度仍不足，而且影响提取漏掉 open-interest 膨胀和 tree-node 消耗；Covenant 则是路由误拒，影响覆盖为零。

逐例重编码及状态枚举见 [SCOPE_ADJUSTED_REVIEW.json](SCOPE_ADJUSTED_REVIEW.json)。以后批次应同时报告核心 P/I/V 分项和逐影响覆盖；不能再用一个全局 `weakened` 取代这两组信息。

## 可改善处

### 1. 先把“核心 claim 忠实度”与“报告覆盖度”分开计分

本批 4 个候选均只选一个直接影响，其他影响在 `limitations` 中明示 deferred。现有评审仍常把遗漏的次级或下游影响直接记为公式 V partial，使 Panoptic 这类“核心 claim 正确、整体覆盖不全”的结果无法与公式方向错误区分。建议之后固定报告两项指标：

- 核心 claim 的 P/I/V 忠实度；
- 原报告直接影响被表达、部分表达、deferred 的覆盖率。

这是评测口径的修正，不需要先改模型规则。

### 2. 再决定是否支持多 claim / 多 impact 输出

GTE Perps、GTE Spot 和 Hybra 都有不止一个重要影响；当前单影响形式计划只能保留一个。本批 3/4 公式 V 的弱化由此得到两位评审共同支持。若阶段二目标要求完整转交报告效果，下一项结构工作应允许一份报告输出多个独立 claim，或为每个未选影响生成有状态的子规格；同时继续允许无法形式化的影响被明确标记为 deferred。不要通过把多个效果塞进单个布尔符号来伪造覆盖。

### 3. 提升结构关系的表达精度

GTE Spot 的报告明确写了 `prevOrderId` 初值为 0、更新只作用于 memory copy、storage slot 未更新；当前规格退化成“较早订单可达”的布尔量。改进重点是让正式关系表达可落到“预期前驱 ID 与 storage 中保存的前驱 ID 对应”，而不是只增加 P 条目。此处也要区分 root-cause 证据与动作前提：根因事实不应为了完整性机械塞进 P。

### 4. 修正可由证据证明的数值门误拒

Covenant 是本批最明确的误拒候选。源文直接给出 `2^noCapLimit` 和 `noCapLimit = 60`，但检查器将有来源的幂表达式折算值 `2^60` 当作报告没有出现的字面量。建议检查器识别**报告中显式写出的、参数有报告内绑定的整数表达式**，保存表达式及其推导来源；只有能从原文确定性推导时才接受折算值。不要普遍放宽“常量必须有报告来源”的门。

## 结论边界

这轮显示最可量化的改善机会是报告影响覆盖和关系结构表达；另有一例候选误拒提示数值表达式解析过严。当前没有观察到反向公式、虚构界限或自比较候选，但 n=5 不足以证明误放行率低。`verify` 通过只确认产物可重放及内部检查一致，不增加忠实度证据。本批完成后不据此改写 `semantic-live`；任何后续修改需单独冻结并重新测量。
