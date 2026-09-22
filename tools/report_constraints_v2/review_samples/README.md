# 公开规范参考样例：先审核含义，再检查公式

日期：2026-09-14。仅新增独立审核材料与离线比较工具；不调用外部模型、不修改第一阶段或历史结果。

## 当前材料的定位

三份练习依据 Certora 公开规范编写。`inputs/` 为助手对官方说明的中文转述，不是原始漏洞报告；`reference.json` 是助手依据公开规范整理的参考 AST，尚待你审核，不能称为专家已验收的标准答案。没有调用 Certora Prover，也没有下载或验证对应合约版本。

来源：

- [ERC20 初始条件教程](https://docs.certora.com/projects/tutorials/en/latest/lesson2_started/preconditions.html)及[配套规范](https://github.com/Certora/tutorials-code/blob/master/lesson2_started/erc20/TotalGreaterThanUser.spec)。
- [两个账户余额之和的规范模式](https://docs.certora.com/en/latest/docs/user-guide/patterns/sums.html)。

规范中的规则不能自动推广到所有 ERC20 实现。前两份练习是状态不变量，第三份是有前提的操作后置性质。都没有报告声称的漏洞效果，V 保留为空，不能凭空补成“真实攻击”。复杂的全账户求和、跨合约、溢出和时序性质暂不纳入。

## 你具体做什么

1. 先读 `inputs/` 中一份中文说明，确认自己理解，再打开 `REVIEW.md` 中对应解释及官方链接。
2. 核对主体、同一代币/状态、条件、比较符号、执行前后位置；不确定的内容写下，不必写 SMT。
3. 在 `REVIEW.md` 勾选认可/需修改/不确定。未勾选前，一律 `pending_user_review`。
4. 若进行模型实验，只给模型自然语言输入，不给 `reference.json`、审核卡或答案。引用的证据应来自实际输入；不能冒充原始英文引文。
5. 模型候选经过语义审核后，将符号按含义与检查点对齐到参考命名，再比较公式。未知映射先停止，不按变量名称猜测。

## 本地比较工具

`check_reference.py` 重用现有 AST 类型检查与 Z3 转换，不改变提取流程。候选文件格式为：

```json
{"preconditions":{"const":true},"safety":{"op":"le","args":[{"var":"balance"},{"var":"supply"}]}}
```

上面仅是 `single_balance` 的公开参考示例，不能用作盲测模型输入。离线自检：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/review_samples/check_reference.py
```

比较另存的候选文件（不调用模型、不写文件）：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/review_samples/check_reference.py \
  --case single_balance --candidate /absolute/path/candidate.json
```

工具分别检查数值域中的 P 是否等价，以及参考 P 下 I 是否等价；SAT 给出差异赋值，UNSAT 表示在该抽象下等价，UNKNOWN 不算通过。定义固定且经人工对齐的符号后才有比较意义。非负数值域是练习的显式背景约束，不是隐藏加入代码语义；不包含 T、EVM 算术、可达性或地址到账户余额的函数关系。参考自检不是模型准确率，更不能证明合约正确。

## 如何发展

先完成这三份审核，再修正 Brix 动作列表并单独做真实复验。练习测试“语言性质到公式”，Brix 测试“报告中推导性质”；两者分别统计。即使练习全部等价，也不能宣布报告提取准确。开源标注样例可能已在模型训练数据中，不作为独立泛化能力证明。

## 本轮验证记录

2026-09-14：V2 共 94/94 回归测试通过（原 84 项，新增 10 项公开规范比较测试）；三份参考 AST 自检均等价；保护检查确认 74 个文件未变。新增测试包含严格比较、方向反转、恒真性质、遗漏不同账户/初始条件、错误检查点、未知变量和非布尔性质。自检与故意修改的反例均为程序控制实验，不是 LLM 成绩。外部模型调用为零，Brix 真实链路仍停在此前记录的结构检查失败。
