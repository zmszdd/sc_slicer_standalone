# 阶段二文档索引

运行入口在上级 [README](../README.md)。本目录只保存设计、状态和历史实验说明，避免与
Python 源码混放。

## 当前必读

| 文件 | 作用 |
| --- | --- |
| `STAGE2_CURRENT_STATUS.md` | 当前完成度、实验结论和未解决问题 |
| `STAGE2_PRESENTATION_REPORT.md` | 面向导师或他人的阶段性汇报 |
| `SECOND_STAGE_DESIGN.md` | 研究目标、方法边界和总体设计 |
| `SAFETY_RELATION_TAXONOMY.md` | 12 类安全关系及确定性模板 |
| `DIRECT_DEEPSEEK_SETUP.md` | DeepSeek 官方 API 配置与隐私要求 |
| `V317_IMPLEMENTATION_REPORT.md` | 当前实验版 v3.17 的实现与回归 |
| `V316_DEVELOPMENT_REPORT.md` | 当前稳定版 v3.16 的开发结果 |
| `V315_RELATION_REPORT.md` | 安全关系分类的本地实现 |
| `V315_DEVELOPMENT_REPORT.md` | v3.15 开发回归 |

## 历史演进记录

这些文件用于解释设计为何演变，不是当前操作入口。

| 文件 | 作用 |
| --- | --- |
| `PROMPT_V3_REPORT.md` | 通用 Prompt v3 设计 |
| `PROMPT_V31_REPORT.md` | v3.1 压缩与留出结果 |
| `PIV_FOCUS_REPORT.md` | P 完整性、I 方向和 V 直接否定关系 |
| `PRECONDITION_AUDIT_V4_REPORT.md` | P 证据/时序审查 |
| `EVIDENCE_IDS_REPORT.md` | 证据编号方案 |
| `EVIDENCE_IDS_REAL_REPORT.md` | 编号方案首次真实复验 |
| `TWO_STEP_REPORT.md` | 早期两步调用记录 |
| `BRIX_RETEST_REPORT.md` | Brix 提示改进复验 |
| `BRIX_CORE_RETEST_REPORT.md` | 核心模式复验 |
| `BRIX_OBSERVABLE_RETEST_REPORT.md` | 可观察变量复验 |
| `REPORT_ONLY_REPORT.md` | 从切片依赖转向报告独立推导 |
| `BATCH_REPORT.md` | 早期本地多样例验证 |
| `AUTO_REPORT.md` | 早期真实自动验证 |

新文档应优先更新当前状态，而不是继续在根目录新增散乱的 `*_REPORT.md`。评测专属报告应
放在对应 `evaluation/<run-id>/REPORT.md`。

## 流程图

- [阶段二流程图与文件索引](STAGE2_FLOW.md)：主流程每步调用的文件与产物、检查门一览
- [stage2_flow.svg](stage2_flow.svg)：上图的可视化版本（由
  [gen_stage2_flow_svg.py](gen_stage2_flow_svg.py) 再生）

（新 SC 生成流程图与整体闭环图已随新 SC 工作废弃删除，2026-10-12。）
