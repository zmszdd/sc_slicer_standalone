# 主线可迁移性配置（2026-11-23）

主线现在通过 `tools/stage3/lib/path_config.py` 解析外部数据路径，避免把当前机器的
`/root/...` 绝对路径写死在协议受控脚本中。配置优先级为：

1. 进程环境变量；
2. `config/paths.local.env`（本地、被 `.gitignore` 忽略）；
3. `config/paths.env`（可选、可提交）；
4. 仓库根目录下的默认值。

支持变量：

| 变量 | 用途 | 默认值 |
| --- | --- | --- |
| `C4_OUTPUT_ROOT` | Code4rena/flattener 输出根目录 | `${SC_ROOT}/c4_pipeline_output` |
| `CODE4RENA_REPORTS_ROOT` | 原始 Code4rena reports 目录 | `${SC_ROOT}/code4rena_reports` |
| `VERIFIED_FLATTEN_ROOT` | 正例 flatten corpus | `${C4_OUTPUT_ROOT}/verified_flatten_pass_1568_exact_cases` |
| `NEGATIVE_FLATTEN_ROOT` | 官方负例 flatten corpus | `${C4_OUTPUT_ROOT}/objective_negative_flatten_1_7_16` |
| `NEGATIVE_FLATTEN_SUMMARY` | 负例 readiness 汇总 | `${NEGATIVE_FLATTEN_ROOT}/input-summary.json` |
| `FORGE_STD_CANDIDATES` | 负例 witness authoring 的 forge-std 候选，冒号分隔 | 空 |

`NEGATIVE_FLATTEN_SUMMARY` 是可选汇总。若文件不存在，`make doctor` 会改为检查
`NEGATIVE_FLATTEN_ROOT` 下是否存在 `*/contract.flattened.t.sol`，避免把缺少报表
误判为环境不可用。

`${SC_ROOT}` 会被替换为仓库根目录。迁移到新机器时复制
`config/paths.env.example` 为 `config/paths.local.env`，填写上述路径，然后运行：

```bash
make doctor
make protocol-check
make locked-eval-check
```

LLM provider 是外部依赖，故意不放入 `make verify`。需要确认额度、鉴权和网络时
单独运行 `make provider-check`；它会在 15 秒内返回可用于 Stage-2 / binding 的
最小 JSON 请求结果，失败时明确区分 401/402/403/429、`GoUsageLimitError` 与网络错误。

该改动只处理外部输入位置，不改样本、标签、verdict、分母或四指标定义。由于
`path_config.py` 已加入协议文件集合，协议 bump 到 `mainline/1.7.23`；在此之前的
run 不再进入当前分母，权威四指标仍需在 1.7.23 下重跑并通过 gate 后才能发布。
