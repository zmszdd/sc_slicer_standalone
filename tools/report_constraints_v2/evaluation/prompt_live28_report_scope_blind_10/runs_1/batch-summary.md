# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-15
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live28_report_scope_blind_10/runs_1

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Brix_Money_qy7NXr77sDh__cSNXN84Wruw__MKMkLQCQdEN | 2 | needs_review |
| Ekubo_3FTodhsvBkM__hXgotbWaKEY__AQB7XkKMuow | 0 | candidate_checks_passed |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__ZBFXjBXfyR2 | 2 | needs_review |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__B42T4SMoQbi__xP5kuw2wBsv | 0 | candidate_checks_passed |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__LDE4mUbttzn__ndavqtk5vRc | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
