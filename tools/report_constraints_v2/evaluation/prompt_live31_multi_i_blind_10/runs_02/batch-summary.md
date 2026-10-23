# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-17
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live31_multi_i_blind_10/runs_02

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Merkl_T4ExvutBBXC__xqZYwzeVXqw__Yc4xRW9vCNx | 2 | needs_input_review |
| Monetrix_L3gNZDymiju__uBJHpCWWngt__a2ihKzkQ4TE | 0 | candidate_checks_passed |
| Olas_j3PRAMM3fVq__zS6WfDd68Ch__6G6KeC9XMg7 | 2 | needs_review |
| Panoptic_Hypovault_c9MhophgwGP__PCEbYiyMPSh__qKC699KEPhD | 2 | needs_review |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__K2yFeuzGwWk | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
