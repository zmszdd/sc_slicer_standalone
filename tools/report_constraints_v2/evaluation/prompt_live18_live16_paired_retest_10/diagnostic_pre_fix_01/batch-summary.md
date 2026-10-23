# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-18
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live18_live16_paired_retest_10/runs_01

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Ekubo_3FTodhsvBkM__BnhskdXG9L2__LWJzDBLXHCX | 2 | needs_review |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__qFXS4TWRDTc__htLr3GYoKEr | 2 | needs_review |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__i74QjxE4Y98 | 2 | rejected |
| Hybra_Finance_xo4hapwL2Jy__Ctj2JAvj8gR__3H5NTm8EgNK | 2 | needs_review |
| Intuition_2VUsxVJwReb__rKaU4cekpfS__AFA3eVn73ez | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
