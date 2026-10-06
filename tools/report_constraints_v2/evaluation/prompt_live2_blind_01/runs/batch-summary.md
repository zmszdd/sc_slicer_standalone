# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live2_blind_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Panoptic__Next_Core_iqcUwAhCZyD__iJDjyjZGS6X__8KUUokLLYwi | 2 | rejected |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | 0 | candidate_checks_passed |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__6bECv5mp6yL | 0 | candidate_checks_passed |
| Hybra_Finance_xo4hapwL2Jy__fsfqfuE2eMf__pNKxUmMc9CA | 2 | rejected |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__WzwMPPEGz4h__6EoX96VUGct | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
