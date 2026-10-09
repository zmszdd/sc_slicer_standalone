# 通用语义 Prompt v3：本地搭建记录

日期：2026-09-14；2026-09-15 完成真实留出集测评。`semantic-v3` 是提示版本，不是第三阶段或新接口版本。

真实结果见 [semantic-v3 新 Prompt 真实留出集测评](../evaluation/archive/prompt_v3_holdout_01/REPORT.md)：5 份新报告、10 次调用、无重试。要素提取五维严格 pass 单元 22/25（助手初评，不是总体准确率），正式 I 和端到端正式化均为 1/5；4/5 在第二次调用超时。结论是自然语言要素理解较好，但当前形式化提示与输入过重，尚不具备稳定批量使用条件。

## 已接入什么

[semantic_prompts.py](../prompts/versions/semantic_prompts.py) 保留现有入口和 schema：默认编号模式仍输出 report-elements/2、report-formalization/2；旧引文模式仍支持 /1；core/full 可用。第一阶段、semantic_pipeline.py、semantic_core.py、report_only.py、SMT/Z3 和接口不修改。现有运行入口自动使用新提示，无新增参数。

第一步明确按主体/场景 → 输入和状态条件 → 根因/效果 → 限定场景的正常义务组织语义。条件可由报告合理推导并标 inferred；不能把实现 guard、成功结果或坏效果直接当攻击前提。类似开关、授权、金额和实际/应有时间阈值分别保留。区分作者声称的条件能力、潜在后果和独立执行证明，不因没有 incident 把全部能力降级。

第二步先写安全义务再构造 AST，限定尝试与完成执行，检查 if/only-if、否定和比较方向，要求可观察变量与派生谓词定义。保留窄范围：不能把特定检查错误扩大为所有交易必须成功或所有正常收益必须禁止。

明确比较节点也是 Boolean 子公式，需要来源路径；子来源必须属于该性质 source_ids，partial/formalized 的影响必须有 V/source 对应。名称、单位、算子、模态与文字/AST 在输出前自查。未知编号、来源、类型等仍由原程序严格拒绝，没有放宽或自动修补。

三个短教学对照为门禁授权、货物等待与费用累积、签名检测误拒绝。没有测试报告名称、数值或参考答案；教学例不是证据，也不是不变量菜单。模型仍自行依据每份报告推导性质。

## 时间单位与范围

当前算术前端要求相同 unit 字符串。对确实以秒计量的时间戳和时长，提示统一 seconds，并在含义和检查点区分绝对时间/持续时间。没有修改类型系统，不允许混合资产或虚构换算来凑通过。数学域假设需明示，不能伪装成原文事实；不宣称无界整数就是 EVM uint256。

不能表达的时序、bitwise、总体或经济影响仍用 null/unresolved 或部分覆盖，不能用一个自由布尔量冒充完整定义。没有消除协议背景缺失或代码绑定需求。

## 版本、成本和历史保护

旧源码已归档到仓库根目录 `archives/stage2_v3_removal_20260922/`；活动目录不再保留第二份快照。

新模块 SHA-256：`c91a8ea3bc206420deb22827fbdd6d9a5c368142f3448d9ded8186c9e814709b`。实际运行保存的 prompt.txt 含 TASK VERSION: semantic-v3，可与历史结果区分；没有增加新的 CLI/schema 字段。

提示字符数（不是 tokenizer 实测 tokens）：

| 默认任务 | 旧版 | 新版 |
| --- | --- | --- |
| 编号要素提取 | 2,044 | 4,472 |
| 编号形式化，core | 4,880 | 8,320 |

提示更长，本轮不声称节省调用 token；仍最多两次调用、无重试。通过简短 JSON/依据避免要求输出长推理，但不能限制服务自身 reasoning 成本。没有新增模型调用，不能宣称 40% 已提高。

保留五报告评估参考、评分、结果和原始模型答案，旧成绩不改写。开发集五份只作错误回归，不能用新提示再跑同一批就称泛化准确率。

## 本地验证

新增 [test_prompt_v3.py](../tests/test_prompt_v3.py) 15 项：版本与 quotes/ids、core/full 兼容；旧快照哈希；无案例答案与示例证据；前提与模态要求；授权/only-if/等待的数学对照；来源路径、单位和旧拒绝保持；两步模拟接入和第一步坏编号仍只调用一次。

模拟回答是已有助手控制，Z3 对照也是人工构造，不计真实模型准确性。原受保护 74 文件检查通过，底层三个关键模块 SHA 与修改前一致。

Prompt 接入时完整回归 **146/146 通过**（原 131 项 + 新增 15 项）；测试中打印的未授权拒绝为预期负向控制。随后真实留出集产生 10 次外部调用，原开发集五报告评分/结果与参考卡未修改。

零模型调用运行本地测试：

```bash
cd /root/sc_slicer_standalone/tools/report_constraints_v2
/root/.local/share/uv/tools/halmos/bin/python -m unittest tests.test_prompt_v3
/root/.local/share/uv/tools/halmos/bin/python -m unittest discover \
  -s tools/report_constraints_v2/tests \
  -t tools/report_constraints_v2 -p 'test_*.py'
```

## 下一步

留出集已按预先冻结参考完成。下一步优先缩减第一步输出和第二步输入，只保留一个核心路径/安全意图/直接影响并允许无法表达时明确弃权；然后在另一组新报告上测 v3.1，保留结构通过、条件完整性、I 语义/公式对应、未覆盖影响等独立指标，失败样例不从分母移除。

不扩大到微调、向量库、多代理或 InvCon/Trace2Inv 主线。后续外部复验仍需单独授权，原审批不当作无限调用许可。
