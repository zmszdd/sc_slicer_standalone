# DeepSeek-V4.1-Flash 阶段二新案例小测（2026-09-18）

## 测试边界

按 [manifest.json](manifest.json) 冻结三份此前未出现在阶段二结果目录的案例 ID，均从 `report.json` 取标题、描述、影响。第一次调用提取编号证据与 P/I/V 要素；第二次仅使用**本次**要素生成形式计划，再做本地校验和 Z3 检查。两次调用的 provider/model 均由 `model-usage.json` 确认为 `deepseek` / `deepseek-flash`（官方 API 对应 V4.1-Flash）；提示版本 `semantic-v3.12`，零重试，不启用机械修复。`--extract` 没有读入历史要素或答案。PoC、修复建议、合约代码以及阶段一、三都未用于本次推导或验证。

## 首次运行结果

| 案例 | 要素校验 | 形式计划 / Z3 | 路由 | 两次模型耗时 | Token 总数 |
| --- | --- | --- | --- | ---: | ---: |
| [Hybra](hybra/status.json) | 通过 | 候选公式 / 已检查 | `needs_review` | 12.58 秒 | 7,221 |
| [Sequence](sequence/status.json) | 通过 | 候选公式 / 已检查 | `needs_review` | 10.88 秒 | 6,968 |
| [GTE](gte/status.json) | 通过 | 被校验拒绝，未进 Z3 | `rejected` | 13.13 秒 | 7,170 |

三份报告的两步 API 请求均返回可解析 JSON（6/6 调用），要素证据校验 3/3，通过形式计划并运行 Z3 2/3；无一被自动确认为语义正确。上述耗时仅为 API 计时相加，不含预览、文件读写和本地复核；三例太少，且非盲评，不能据此估计总体准确率。

## 对照原文的抽查

- **Hybra：**要素层抓住“非首次存款、先锁仓后计算、份额少发”及 100/50 示例。但生成的 I 是 `lock_before_calc ⇒ ¬shares_underminted`，`shares_underminted` 本身是未拆解为可观察数值关系的布尔标签；它没有表达 `mintedShares < depositAmount × preSupply / preAssets` 一类报告所需的量化比较。因此 Z3 的 P∧V∧I 不可满足只证明自造公式互斥，**不能证明准确提取了报告的不变量**。
- **Sequence：**要素层抓住“直接调用、路由器持有余额、攻击者指定目标并获批/转出”。但 I 的条件被压缩成 `router_funds_present ⇒ ¬router_approves_target_balance`，丢失“**直接调用而非合法 delegatecall**”的限定，可能错误禁止合法代理上下文中的操作；且核心 V 只保留授权，未形式化实际资产流失。Z3 同样不能填补这一语义缺口。
- **GTE：**要素层识别了 `quoteAsset` 与 `rs.quoteAsset` 不匹配、零 launch 金额及 USDC 被取走的声称。第二步计划引用 `claim_drains_usdc` 作为真假谓词，但未在 `symbols` 中声明，触发 `invalid truth binding`。这是程序正确拒绝了未定义符号，不能计为完成形式化。原文对 claim 转账机制也缺细节，不能凭空补公式。

## 结论与下一步

DeepSeek-V4.1-Flash 的阶段二两步调用、证据回填、形式计划及本地 Z3 链路能在部分新报告上跑通；当前主要瓶颈从 API 连通性转为**公式的语义忠实度与可观察性**。优先要求核心 I/V 包含报告支持的可观察变量及关键限定（时间点、调用上下文、资产量）；对无法建立此绑定的结果保留 `needs_review`/拒绝。下一轮须冻结规则后用更多独立新案例，并将“工程完成率”“证据支持率”“逐条语义正确率”分开统计。不要将 `P∧V∧I = unsat` 当作准确率。

本次没有修改阶段一或阶段三，未把任何案例标为真实漏洞或 PoC 一致。

## 后续离线筛选（不改写上述首次成绩）

新增的[多维筛选结果](SCREENING.json)只复核已保存的输入和输出，未调用模型：
Hybra、Sequence 为 `continue_with_review`，表示证据、核心公式和逻辑关系可供后续复核，
**并不推翻上文发现的语义缺陷**；GTE 为 `retain_elements_defer_formalization`，
表示保留已取出的 P/I/V 要素，暂缓无效公式。筛选不会删除原案例，
也不能从这三例推断总体准确率。
