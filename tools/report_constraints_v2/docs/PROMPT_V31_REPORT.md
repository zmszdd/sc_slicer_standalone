# P/I/V Prompt v3.1：预算化改进记录

日期：2026-09-15。状态：本地实现与真实新留出集测评完成。

真实结果见 [v3.1 留出集报告](../evaluation/archive/prompt_v31_holdout_01/REPORT.md)：5 份新报告实际调用 9 次，第一步完成 4/5、第二步回答 3/5、正式管线完成 1/5；正式 I 为 0 pass、2 partial、3 fail，完整 P/I/V 为 0/5。v3.1 尚未达到准确提取 P/I/V 的目标。

为检查错误一致性，又用不改 Prompt 的[第三批五报告](../evaluation/archive/prompt_v31_consistency_02/REPORT.md)运行 10 次：无超时，正式管线 4/5，正式 I 初评 3/5，但完整 P/I/V 仍只有 1/5。P 缺失/污染、V 不能见证 `not I`、模态升级均重复；schema 缺失与超时未稳定复现。

## 目的

v3 留出集显示：报告要素五维严格 pass 单元为 22/25，但正式 I 和端到端完成只有 1/5；另外 4 份都在第二次形式化调用达到 240 秒超时。v3.1 不增加漏洞规则或工具，专门把任务收敛到用户需要的一个核心 P/I/V。

## 已完成

- 新增 [semantic_prompts_v31.py](../prompts/versions/semantic_prompts_v31.py)，保留
  [semantic_prompts.py](../prompts/versions/semantic_prompts.py) 作为可重放的 v3，后者
  SHA-256 仍为 `c91a8ea3bc206420deb22827fbdd6d9a5c368142f3448d9ded8186c9e814709b`。
- `semantic_pipeline.py` 可用 `--prompt-version semantic-v3.1` 运行本实验；真实测评后，因完整 P/I/V 为 0/5，默认入口已切回规则更完整的 `semantic-v3`。
- 第一调用限制为最多 8 个实体、12 个 statement，并明确只提取一个核心安全意图、至多两个直接影响。
- 第二调用在 core 模式要求一个核心 claim、最多 8 个符号；继续严格区分 P 来源、I 来源和 V 来源。
- 保留观察量、执行限定、蕴含方向、比较严格性、类型/单位、证据编号、子公式来源和 `null + unresolved` 规则。
- 第二调用只携带第一步实际引用的证据片段。该裁剪是机械过滤，不选择或改变语义事实。
- 批处理入口记录并转发 `prompt_version`，仍保持最多两次调用、无自动重试。

未修改 `semantic_core.py`、`report_only.py`、Z3/SMT 校验器、第一阶段、Rust/Solar 或 `run.sh`。

新增 7 项 v3.1 回归后，第二阶段完整本地测试为 **158/158 通过**；受保护文件检查为 **74/74 未变化**。v3.1 模块 SHA-256 为 `8c661155868411f9c6668b25a4bd954d97ea9e8d28bfe996802e81323b71e331`。

## 本地量化

| 编号模式 | v3 字符数 | v3.1 字符数 | 降幅 |
| --- | ---: | ---: | ---: |
| 要素提取 Prompt | 4,472 | 2,425 | 45.8% |
| core 形式化 Prompt | 8,320 | 3,748 | 55.0% |

将证据过滤机械应用到 v3 已保存的五份要素上，第二步 payload 只减少约 0%–2.3%，因为旧输出几乎引用了全部报告片段。因此主要收益应来自新提示对第一步实体/statement 数量的限制，而不是证据过滤本身。上述字符数不是 tokenizer token 数，也不能证明真实耗时已经下降。

## 使用

显式运行 v3.1：

```bash
/root/.local/share/uv/tools/halmos/bin/python \
  tools/report_constraints_v2/semantic_pipeline.py \
  --report REPORT.json --extract --allow-report-upload \
  --model opencode-go/deepseek-v4-flash --prompt-version semantic-v3.1 \
  --output NEW_OUTPUT
```

当前默认 v3，也可显式指定：

```bash
... semantic_pipeline.py ... --prompt-version semantic-v3
```

批处理也支持 `--prompt-version semantic-v3.1|semantic-v3`，当前默认 v3。

## 当前边界与下一步

新的外部留出集已经运行，但样本小、评分未经专家确认，仍不能宣称总体准确率。下一步只针对漏 schema 字段、potential 模态升级、`eq` 弱化和 V 不蕴含 `not I` 做 v3.2 小修；当前五份转为失败回归，不能反复调参后再把其成绩称作泛化结果。
