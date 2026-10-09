# semantic-v3.16 独立留出集报告

## 结论

冻结的 5 份全新报告全部通过输入筛选并生成合法 P/I/V 要素；3 份形成最终形式化候选并
可带警告继续，工程完成率为 **3/5（60%）**。对 3 份候选独立复核后，严格 P/I/V 全部
忠实的为 **1/3**，三项均达到 pass 或 partial 的为 **2/3**。这不是专家金标准或总体准确率。

相较 v3.15 第二批的 1/5 工程完成，固定模板、派生定义和局部修复改善了稳定性；但 Merkl
仍说明“候选完成”可能隐藏关键攻击条件缺失，不能以 Z3 或完成率代替语义准确率。

## 冻结与输入

[SELECTION.json](SELECTION.json) 在调用前保存了 5 份报告的输入哈希、Prompt 哈希及核心
实现哈希，并排除 45 个既有案例 ID。测试使用 DeepSeek `deepseek-flash` 完整执行输入
筛选、要素提取、形式化和最多两次字段级局部修复。查看结果后未修改冻结的 v3.16。

## 工程结果

| 报告 | 要素 | 最终候选 | 可继续 | 结果 |
|---|---:|---:|---:|---|
| GTE LaunchToken rewards | 成功 | 否 | 否 | 数值 P 完整性检查持续失败 |
| Intuition AtomWallet | 成功 | 否 | 否 | ERC-4337/EIP-191 被误识别为数值 P |
| Merkl operator griefing | 成功 | 是 | 是 | `needs_review` |
| Sequence router theft | 成功 | 是 | 是 | `needs_review` |
| SukukFi vault unregistration | 成功 | 是 | 是 | `needs_review` |

Intuition 是确认的机械误拒绝：协议标准编号并非数值约束。GTE 报告信息也足够，但模型遗漏
了另一条含 `totalFeeShare = 0` 的前提；严格 P 检查拒绝具有合理性。因此统一记为“适合
输入未完成 2/5”，其中确认误拒绝 1/5。

## 语义复核

机器可读复核见 [SEMANTIC_REVIEW.json](SEMANTIC_REVIEW.json)。

| 报告 | 要素 P/I/V | 分类 | 公式 P/I/V | 主要问题 |
|---|---|---|---|---|
| GTE | pass/pass/pass | 不可评价 | 不可评价 | 没有最终候选 |
| Intuition | pass/pass/pass | 不可评价 | 不可评价 | 标准编号触发数值误拒绝 |
| Merkl | partial/pass/pass | pass | fail/fail/fail | 公式要求创建者余额充足，与提现后的真实攻击状态相反 |
| Sequence | pass/pass/pass | pass | partial/pass/pass | delegatecall 前提被重复映射成 public-callable 布尔量 |
| SukukFi | pass/pass/pass | partial | pass/pass/pass | 分类标签偏宽，但 P/I/V 关系忠实 |

要素层仍明显优于公式层：5 份的 I、V 文本均有报告支持，P 为 4 pass、1 partial。严格
公式正确为 1/3，说明形式化忠实度依然是阶段二的主要准确率瓶颈。

## 效率

- 外部模型有效响应：20 次；
- 累计模型耗时：115.67 秒，平均约 5.78 秒/响应；
- 累计 tokens：88,093（prompt 69,366，completion 18,727）；
- cache hit tokens：40,448；
- 三份完整候选均通过离线零调用重放。

## 后续问题

1. 数值扫描需排除 ERC-4337、EIP-191 等标识符，并区分“未选中的旁支数值 P”和当前核心
   claim 必需的数值 P；此修复必须进入新版本，不能回写本留出集。
2. 形式计划应检查所选 impact 中的攻击限定是否进入 condition，避免 Merkl 式错误作用域。
3. 一个 P 来源不应与另一语义不同的 P 共用同一个布尔谓词；应增加来源到谓词的区分检查。
4. 扩大新留出集和独立人工审核前，不能把 1/3 外推成项目准确率。
