# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live10_blind_20/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Brix_Money_qy7NXr77sDh__cSNXN84Wruw__8p7p8cgawcC | 2 | needs_review |
| Virtuals_Protocol_hzMS6ZZkBTg__yc36fBWWe3H__jrMhUzQFvnU | 2 | needs_review |
| Morpheus_kdPtwopH6ws__frkcGbwAqGW__cWxqBprb2Ss | 0 | candidate_checks_passed |
| SukukFi_syLyTBz5KNA__ZB6gasSVLet__TXLXeDriwY2 | 2 | needs_review |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__WxFog2dKdF8__4aKMbik3PdQ | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
