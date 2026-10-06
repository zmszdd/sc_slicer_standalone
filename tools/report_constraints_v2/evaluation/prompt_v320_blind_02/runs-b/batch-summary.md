# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-v3.20
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_v320_blind_02/runs-b

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__9ZcjDfx5VLP | 0 | candidate_checks_passed |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__QW9maHr29yd__GbLSjUaMdqD | 2 | needs_review |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__3JLZHNX2ry4 | 0 | candidate_checks_passed |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__hqm4CJJttHi | 0 | candidate_checks_passed |
| Covenant_d4uY8y2AMSs__otmbJXz4irq__6R7dHjZmMwv | 2 | rejected |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
