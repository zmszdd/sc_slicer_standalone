# 阶段二第二步稳定性复验（Sequence + GTE）

日期：2026-09-16。复用旧盲测已保存且通过证据校验的 `elements-ids.json`，
只运行真实模型的第二步；输入是归档的公开非敏感 `report.json`。
使用 `semantic-v3.7`，不上传合约或 PoC，不人工修补模型输出。

| 案例 | 旧盲测第二步 | 本次环境/调用 | 本次形式化与 Z3 | 自动路由 |
| --- | --- | --- | --- | --- |
| Sequence | 空响应 | 可访问环境，1 次，83.091 秒，21,399 tokens | 完成 | `review` |
| GTE | int 单位/schema 错误 | 可访问环境，1 次，56.531 秒，8,761 tokens | 完成 | `review` |

两例的报告级数学查询均为 `P∧V=SAT`、`P∧V∧¬I=SAT`、`P∧V∧I=UNSAT`。
这证明本次生成公式内部可构造直接反例，**不证明报告语义准确或 PoC 一致**。
两例均未触发第二次模型调用，因此本次不能量化重试机制在真实模型上的收益。
新输出分别在 `results/semantic/diagnose_sequence_v37_02/` 与
`results/semantic/diagnose_gte_v37_01/`；旧盲测输出未修改。

GTE 仍有实质问题：形式 P 未使用已提取的 `p_dust_unfilled`；`only_dust_remainder`
目前是报告级布尔抽象，而非可观察的 lot-size 数值关系；次级 availability 影响延期。
Sequence 的永久 DoS 影响延期，且报告/计划留有歧义。两例应保留 `review`，
不能因 Z3 通过升级为自动语义确认。

本次是两个**已知失败案例**的第二步复验，不是随机样本、完整两步新盲测或总体准确率。
受限终端仍可能令外部 CLI 提前退出；模型服务的可用性评测必须固定执行环境。
