# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-v3.20
- 案例数: 5（新跑 0，续跑跳过 5）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_v320_blind_02/runs-a

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__R545AgjZpJm | None | rejected |
| Merkl_T4ExvutBBXC__btqEyvckPQN__X2HQE9uKsCs | None | rejected |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__oDzJS5GtCHY | None | rejected |
| Panoptic__Next_Core_iqcUwAhCZyD__mcDESyXf24Q__CkMtbbVR8o5 | None | candidate_checks_passed |
| Panoptic_Hypovault_c9MhophgwGP__MoUD6X4jmfD__b3JuyroVfQn | None | rejected |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
