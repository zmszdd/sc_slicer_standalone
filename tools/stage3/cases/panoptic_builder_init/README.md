# panoptic_builder_init

真实 code4rena 案例：`2025-12-panoptic`（Panoptic Next Core，audit uid
`iqcUwAhCZyD`）finding 17（finding uid `CUEQdPu878N`）。

**漏洞**：`BuilderWallet.init` 是公开函数且没有任何访问控制，任意调用者都能在部署后
覆盖 `builderAdmin`，随后用 `sweep` 把钱包里累积的 builder 手续费转走。

**来源**

- 源码：`c4_pipeline_output/_github_repos/code-423n4__2025-12-panoptic__a4361d6d8dc6420c09187d80ea1a7ce851d1ca36/contracts/RiskEngine.sol` 的
  `IERC20` / `BuilderWallet` / `Create2Lib` / `BuilderFactory` 块（第 2296-2410 行）。
- `Errors`：同仓库 `contracts/libraries/Errors.sol`，逐字拷贝。
- 阶段二 run：`tools/report_constraints_v2/results/semantic/stage3_smoke_01/run`
  （`stage3-spec.json` / `constraints.json` / `formalization.json`）。

**注意**：`code-423n4/2025-12-panoptic` 主分支的 `init` 没有
`AlreadyInitialized` 一次性守卫，漏洞真实存在；Panoptic Hypovault 仓库后来补了守卫，
因此不要用 Hypovault 仓库的 `Builder.sol` 跑这个案例。

**符号绑定**

- `init_publicly_callable` → `true`（`init` 为 public 且无守卫，静态事实）。
- `caller_is_any_eoa` → `msg.sender != FACTORY`（调用者不是授权工厂）。
- `builder_admin_overwritten` → `builderAdmin == msg.sender`（调用者把自己设为 admin）。

补丁注入到 `BuilderWallet.init`，断言 `!(P) || !(V)`：授权工厂初始化路径通过，
非工厂调用者在覆盖 admin 后触发断言失败。

**运行**

```bash
cd /root/sc_slicer_standalone
/root/.local/share/uv/tools/halmos/bin/python main.py stage3 \
  --case-dir tools/stage3/cases/panoptic_builder_init \
  --run-id panoptic_builder_init_001
```

预期：`consistency_verdict = violation_reproduced`。
