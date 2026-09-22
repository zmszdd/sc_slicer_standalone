# `report.json` 输入重新测评

日期：2026-09-16。模型：`opencode-go/deepseek-v4-flash`。Prompt：`semantic-v3.2`。
同一批三份冻结报告，最多两次调用/案例，无失败重试、无人工修补。参考沿用
`../prompt_v32_ab_01/REFERENCE.md`，未发送给模型。本报告为助手初评，不能作为总体准确率。

## 结论

新的 `report.json` 字段白名单正确隔离了代码侧输入，但本轮没有跑通完整形式化链路，
也没有证据表明 P/I/V 准确率因输入切换而提高。

| 指标 | 结果 |
| --- | ---: |
| `report.json` 白名单与 provenance | 3/3 |
| 合约未读取、代码/PoC 未提供模型 | 3/3 |
| 第一步要素提取完成 | 3/3 |
| 自然语言核心 I 初评通过 | 3/3 |
| 自然语言核心 V 初评通过 | 3/3 |
| P 完整性严格通过 | 0/3 |
| P 角色纯度严格通过 | 0/3 |
| 第二步返回候选 | 1/3 |
| 完整形式化与 Z3 | 0/3 |

Sukuk 与 Hybra 的第二步均在 240 秒上限超时。GTE 返回了形式候选，但 claim 的
`impact_ids` 使用不存在的 `fok_fill_reverted`，校验器以 `invalid claim impacts` 拒绝，
因此不能进入 Z3。三例均调用两步，共六次尝试；仅四个已完成步骤留下 usage，合计
36,487 tokens、估算 0.014529054。两个超时步骤可能产生未记录消耗。

## 分案例判断

### Sukuk

- P 捕获了受害者存款、self-allowance、外部调用者非 owner 且无授权。
- 仍缺攻击者控制 receiver、提款份额/授权量关系；把“接口接受任意 owner”标成 P。
- 自然语言 I 正确表达 owner 或足额授权才能提款，V 能表达未授权提款完成。
- 报告声称攻击者可以盗取，模型却把资金被抽走标成 `potential`，仍有模态降级。
- 第二步超时，正式 I/V 不可评价。

### Hybra

- 捕获存款、即时提款、默认零 maturity 和 flash-staking 潜在影响。
- P 中混入 mapping 未初始化、默认零、比较恒真等实现根因/推导结果；缺少正提款量和
  “早于 intended maturity”这一关键前提。
- 自然语言 I 正确要求达到用户应有 maturity 后才能完成提款，V 正确描述即时提款；
  flash-staking 保持 potential，没有升级。
- 第二步超时，正式 I/V 不可评价。

### GTE

- 捕获 FOK dust 场景、不回退意图和实际回退，核心自然语言 P/I/V 基本同向。
- 把协议文档中的安全意图 `pre_dust_allowed` 同时标成 P，P 角色仍不纯。
- 正式 I 为 `dust_only_unfilled -> not reverted`，V 为 dust 与 revert；逻辑方向合理，
  但 dust/revert 都是待绑定布尔观察量，且没有区分具体回退原因。
- 候选引用未提取的 impact ID，被 schema 正确拒绝；这属于第二步引用一致性错误。

## 输入切换本身的问题

隔离目标已经实现：provenance 明确记录 `contract_file_read=false`、
`code_provided_to_model=false`，输入只来自 `title` 与筛选后的 `body`。

但 Sukuk 和 Hybra 的 `report.json.title` 与 `body` 第一行标题重复，当前拼接器将两者都保留，
造成标题重复。GTE 正文没有重复标题，所以未出现。下一步应在输入预处理层对
`title` 与正文首个 H1 做规范化去重；该问题不需要修改 Prompt 或底层约束逻辑。

## 客观判断

本轮证明 `report.json` 可以作为独立、可追溯且不泄露 PoC/代码的阶段二输入；没有证明
准确率提升。自然语言 I/V 的方向较稳定，P 分类仍是首要语义瓶颈；第二步的超时和 ID
引用错误则是当前端到端完成率的直接瓶颈。旧 v3.2 批次曾完成 3/3，本轮为 0/3，
由于模型生成随机性、服务时延和输入标题变化，不能把差异单独归因于 `report.json`。

原始输出位于 `../../results/semantic/prompt_v32_report_json_03/`，逐项评分见
[`ratings.json`](ratings.json)。前两次中断/启动失败目录不纳入本报告。
