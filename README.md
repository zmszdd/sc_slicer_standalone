# SC_Slicer

SC_Slicer 是一个面向 Solidity 合约的目标导向代码切片工具。当前推荐使用 `run.sh` 入口运行，它会按指定的输入文件、目标合约、目标测试函数和目标变量生成切片合约，并可自动用 Foundry 复跑目标测试。

## 快速运行

在项目根目录执行：

```bash
cd /root/sc_slicer_standalone
./run.sh
```

默认目标是当前 PoC：

```text
输入文件: ./examples/src/poc_final.t.sol
目标合约: PoC
目标测试: test_submissionValidity
目标变量: availableForWithdrawal
模式:     resurrect-v2
层级:     0
```

等价核心命令是：

```bash
cargo run --release -- ./examples/src/poc_final.t.sol PoC availableForWithdrawal \
  --target-test test_submissionValidity \
  --aggressive-cleanup \
  --resurrect-v2 \
  --max-level 0 \
  -o ./results/<run-id>.sol
```

## 输出文件

不指定 `-o/--output` 时，脚本会自动生成唯一文件名，避免覆盖历史结果。

一次运行会生成类似下面的文件：

```text
results/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.sol
results/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.sol.v2.json
logs/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.log
logs/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.forge-test.log
foundry_runs/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345/
```

含义：

```text
.sol                 切片后的合约源码
.sol.v2.json         v2 切片元数据，包括 compile_success、last_command 等
.log                 slicer 运行日志
.forge-test.log      目标 forge test 日志
foundry_runs/.../    本地 Foundry 验证工程
```

## 自定义输入参数

推荐直接通过命令行参数传入，不需要修改脚本。

参数对应关系：

```text
-i, --input FILE       输入 Solidity 文件
-c, --contract NAME    目标合约名
--fn NAME              目标测试/函数名，会传给 --target-test
-v, --variable NAME    目标变量名
-l, --level N          最大依赖层级，对应 --max-level
-o, --output FILE      指定输出文件；不指定则自动生成唯一文件名
```

例如，分析另一个文件、合约、测试函数和变量：

```bash
./run.sh \
  --input ./examples/src/poc_final.t.sol \
  --contract PoC \
  --fn test_submissionValidity \
  --variable availableForWithdrawal \
  --level 0
```

如果希望输出到固定文件：

```bash
./run.sh \
  -i ./examples/src/poc_final.t.sol \
  -c PoC \
  --fn test_submissionValidity \
  -v availableForWithdrawal \
  -o ./results/my_slice.sol
```

注意：指定固定 `-o` 会覆盖同名文件。日常跑实验建议不传 `-o`，让脚本自动命名。

## 常用运行方式

生成 v2 切片并复跑目标测试：

```bash
./run.sh
```

只生成切片，不额外复跑 `forge test`：

```bash
./run.sh --no-rerun-test
```

默认情况下，脚本会把可复跑的 Foundry 工程放在项目内：

```text
./foundry_runs/<run-id>/
```

该目录会包含：

```text
foundry_runs/<run-id>/ResurrectedV2.t.sol
foundry_runs/<run-id>/foundry.toml
```

之后可以手动复跑：

```bash
forge test --root ./foundry_runs/<run-id> \
  --match-contract PoC \
  --match-test test_submissionValidity \
  --via-ir
```

如果想指定自己的 Foundry 工程目录：

```bash
./run.sh --manual-project ./foundry_runs/my_verify_project
```

## 运行模式

默认使用 `--resurrect-v2`：

```bash
./run.sh --v2
```

只做快速切片，不做复活：

```bash
./run.sh --quick
```

开启 v2 的更宽松编译保证：

```bash
./run.sh --compile-guarantee
```

## 验证结果

运行完成后，终端会打印实际输出文件、元数据文件、测试日志和可复制的手动验证命令。

成功时应看到类似：

```text
[PASS] test_submissionValidity()
Suite result: ok. 1 passed; 0 failed
```

也可以查看对应的元数据：

```bash
cat results/<run-id>.sol.v2.json
```

其中关键字段：

```text
compile_success: true 表示切片结果编译/测试通过
slice_effective: true 表示没有退化成完整源文件
last_command          记录实际执行的 forge test 命令
```

## 查看帮助

```bash
./run.sh --help
```
