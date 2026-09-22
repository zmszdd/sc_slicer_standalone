# 阶段二清理归档（2026-09-22）

这些文件已退出当前阶段二工作流，为保留历史恢复能力而从活动目录移动到这里：

- `prepare_observable_demo.py`：只生成早期演示数据，无运行时或测试调用者；
- `verify_report_only.py`：只验证早期 report-only 产物，当前使用 `verify_semantic.py`；
- `INCIDENT_20260922.md`：一次历史误删事故记录；
- `README_before_cleanup.md`：精简前的阶段二长 README，包含逐版本历史叙述。
- `reference_cases/`：早期 Prompt 设计使用的公开教学参考案例，当前运行和测试均不依赖。

当前入口、结构和方法说明以 `tools/report_constraints_v2/README.md`、`STRUCTURE.md`、
`docs/STAGE2_CURRENT_STATUS.md` 和 `docs/SECOND_STAGE_DESIGN.md` 为准。
