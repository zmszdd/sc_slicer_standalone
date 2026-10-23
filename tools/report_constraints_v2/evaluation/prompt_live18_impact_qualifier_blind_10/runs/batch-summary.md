# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live18_impact_qualifier_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__QW9maHr29yd__VGGRDDZZYpi | 2 | needs_review |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__ATCfTSSPjAZ | 2 | needs_review |
| Intuition_2VUsxVJwReb__vtU4cDUiiDR__HzseyTKRxhg | 2 | rejected |
| Kinetiq_k8aVPPVguSE__5Sztw6hvQSr__N9iucpLsprJ | 2 | needs_input_review |
| Merkl_T4ExvutBBXC__r4uzVTfnNHG__bmuAjNumB4q | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
