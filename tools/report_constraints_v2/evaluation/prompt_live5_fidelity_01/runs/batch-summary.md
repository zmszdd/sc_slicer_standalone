# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live5_fidelity_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Panoptic__Next_Core_iqcUwAhCZyD__khDFMWb5Zuo__krhc2oEX9UE | 0 | candidate_checks_passed |
| Covenant_d4uY8y2AMSs__Jk2Mbvck9TA__XnZiMyMpRjs | 2 | rejected |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__B42T4SMoQbi__bXR4nfCANnV | 0 | candidate_checks_passed |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__tbFZqodqgQe | 0 | candidate_checks_passed |
| Hybra_Finance_xo4hapwL2Jy__Rgrwi55pufk__73CEJ2K7Fkm | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
