# semantic-v3.15 第二批独立小规模留出测试

本批继续使用冻结的 v3.15 规则，从未出现在既有阶段二 manifest/provenance 中的报告里
确定性选择 5 个不同项目。选择清单、输入哈希、Prompt 哈希和核心实现哈希保存在
`SELECTION.json`。

本批只用于复测工程完成率、关系分类、P/I/V 公式忠实度和误拒绝。Z3 通过不计作语义正确，
查看结果后不修改本批使用的生成规则。

测试已完成，结果见 [REPORT.md](REPORT.md)，机器可读复核见
[SEMANTIC_REVIEW.json](SEMANTIC_REVIEW.json)。本批 5/5 生成合法要素，1/5 生成最终候选；
唯一候选仍有关键公式忠实度错误。
