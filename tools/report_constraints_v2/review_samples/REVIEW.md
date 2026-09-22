# 逐条人工审核卡

所有条目状态：`pending_user_review`。以下解释由助手整理，不是你已经认可的答案。参考公式留在审核侧，不放进模型提取输入。

## 1. single_balance：账户余额不超过供应量

来源：[Certora 教程](https://docs.certora.com/projects/tutorials/en/latest/lesson2_started/preconditions.html)。

- 范围：同一代币、同一状态、任意选定账户。
- P：没有额外业务前提；非负整数作为显式背景数值域。
- I：`balance <= supply`。例如余额和供应量都是 10 时允许成立，因此不能写成严格小于。
- V：空，原文是规范，不是漏洞报告。
- 注意：一个账户的约束不等于“总供应量等于全部账户余额之和”。任意账户的普遍含义保留在范围描述中；本地公式只检查任意选定账户的数学观察值，不完成全状态归纳证明。

你的审核：

- [x] 认可上述含义和条件。
- [ ] 需要修改。
- [ ] 不确定，暂不作为已确认参考。

意见：

## 2. two_balances：不同账户的余额和

来源：[Certora Tracking Sums](https://docs.certora.com/en/latest/docs/user-guide/patterns/sums.html)。

- 范围：同一代币、同一状态、任意两个不同账户。
- P：`account_a != account_b`；金额非负作为显式背景数值域。
- I：`balance_a + balance_b <= supply`，在 P 下成立。
- 等价组织方式：把不同账户条件放进 I 的蕴含式。当前参考为了审核方便将条件拆为 P；比较前需要统一组织方式，而不是机械比较字符串。
- V：空。
- 注意：不能遗漏“不同”。同一账户的余额可能为 6、供应量为 10，重复相加为 12 不代表代币出错。这里不假设任意两个观察量之间已经满足 I，否则会把正确答案偷偷放入背景约束。

你的审核：

- [x] 认可上述含义和条件。
- [ ] 需要修改。
- [ ] 不确定，暂不作为已确认参考。

意见：

## 3. mint_postcondition：带前提的操作后置性质

来源：[Certora 配套规范](https://github.com/Certora/tutorials-code/blob/master/lesson2_started/erc20/TotalGreaterThanUser.spec)，对应 `totalSupplyAfterMintWithPrecondition`。

- 范围：同一代币、同一接收账户、mint 调用前与正常返回后。
- P：`supply_before >= balance_before`，且 mint 正常返回是后置检查的范围条件。
- I：`supply_after >= balance_after`。
- V：空。
- 注意：这是后置性质，不是仅凭这条规则就证明全局不变量。调用前总量与调用后余额混着比较属于检查点错误；把初始条件删掉也改变了参考规则含义。此处不额外推导 mint 增量、不执行合约、不讨论回退调用的后置状态。

你的审核：

- [x] 认可上述含义和条件。
- [ ] 需要修改。
- [ ] 不确定，暂不作为已确认参考。

意见：
