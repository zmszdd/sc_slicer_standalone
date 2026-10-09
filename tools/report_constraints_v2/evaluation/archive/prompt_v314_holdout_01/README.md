# semantic-v3.14 独立留出集

本目录在任何模型调用前冻结 10 份未出现在既有阶段二 manifest/provenance 中的报告。
选择规则固定为：`report-json-input/4` 后正文 600..4500 字符、精确配对、每个项目最多
一份，再按 `sha256("stage2-v314-independent-2026-09-19:" + case_id)` 升序选择。

`SELECTION.json` 保存选择依据与输入哈希；两个批次文件各含五例，以保持批处理器的调用
上限。测试只发送标题、描述和影响，不发送 PoC、修复建议或合约代码。该批次在结果生成
前没有 P/I/V 标准答案，不能在查看输出后修改选择。

测试已完成。完整结果、效率、逐例 P/I/V 复核和错误归因见 [REPORT.md](REPORT.md)；机器可读
复核记录见 [SEMANTIC_REVIEW.json](SEMANTIC_REVIEW.json)。当前结果为 8/10 合法要素、7/10
形式候选与 Z3、6/10 可带警告继续。该完成率不等于语义准确率。
