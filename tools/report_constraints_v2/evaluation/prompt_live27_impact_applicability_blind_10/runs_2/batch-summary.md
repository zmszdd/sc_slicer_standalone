# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-14
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live27_impact_applicability_blind_10/runs_2

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| SukukFi_syLyTBz5KNA__yZs283iFYxR__K8iEhnzEysb | 2 | needs_review |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__deVmwC5DHi7 | 2 | needs_review |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__WzwMPPEGz4h__vuyPaaLuUXu | 2 | needs_review |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__8j5nFX9rNe8 | 0 | candidate_checks_passed |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__jczYF4pgf3U | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
