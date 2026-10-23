# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-14
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live26_impact_applicability_blind_05/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__rjL9FdNnrCk | 2 | needs_impact_review |
| Intuition_2VUsxVJwReb__vtU4cDUiiDR__wC4QDwrRjko | 2 | excluded_before_extraction |
| Olas_j3PRAMM3fVq__zS6WfDd68Ch__eQ6JLM2YprU | 0 | candidate_checks_passed |
| Intuition_2VUsxVJwReb__vtU4cDUiiDR__Bqc899ejHRp | 2 | rejected |
| SukukFi_syLyTBz5KNA__eJytFti7FNb__c3gncNUSyd3 | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
