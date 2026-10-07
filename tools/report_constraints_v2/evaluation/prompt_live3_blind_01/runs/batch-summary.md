# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live3_blind_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__WEBk6P7Cobd | 0 | candidate_checks_passed |
| Merkl_T4ExvutBBXC__r4uzVTfnNHG__s3EuJSsvvaT | 0 | candidate_checks_passed |
| Intuition_2VUsxVJwReb__vtU4cDUiiDR__WXg7AhCDSNC | 2 | rejected |
| Brix_Money_qy7NXr77sDh__cSNXN84Wruw__SRWcRggMaAn | 0 | candidate_checks_passed |
| Kinetiq_k8aVPPVguSE__NcLiSxr4kBa__eRx6RdN6ipj | 2 | needs_input_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
