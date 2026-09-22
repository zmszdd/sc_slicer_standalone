# 五报告小样本预先评估参考

状态：assistant_preliminary_reference，尚未经用户或独立专家审核。2026-09-14，在本批模型调用前依据描述和影响整理，不读 PoC，不读取本批模型答案。此文件不发送给提取模型。公开报告的 valid/invalid 标签不作为提取准确性标准。

抽样：五个不同项目、五个不同 finding；选取短报告及清晰的窄核心义务，非随机总体样本。不纳入 Brix 重复调试样例。Blackhole 的“50% 即下溢”涉及条件歧义，本批不作参考。这里评估报告主张，不认证合约实现或漏洞真实性。

## 固定评分维度

每份分别记录六项：范围/主体、核心前提、安全意图、I 的形式化对应、核心 V、范围/语气与未覆盖影响。取值 pass/partial/fail/not_evaluable；partial 不能当完整正确。结构拒绝的输出仍可只读审核原始语义，但不能计正式链路成功。缺少公式记 not_evaluable；自动 I 成功率以全部五份为分母，不排除失败样本。

整体完整通过要求六项都是 pass。单独报告“核心 I 合理”比例和程序结构/证据、正式 SMT/Z3 链路成功比例；不能把软件测试数量当语义准确率。公式允许等价表达，不能按变量名或字符串机械判错。观察量与原文的映射由助手解释，Z3 只作数学诊断。复杂或歧义的更广经济/时序影响单列，不作全覆盖 gold answer。

## kinetiq_pause：提款专用暂停

原文明确：两种确认函数有通用暂停检查，却缺提款专用暂停检查；排队提款需满足 delay，提款专用暂停仍可确认并提取 HYPE。

- P：排队提款已满足延迟，通用合同未暂停，提款专用开关暂停；其他有效条件未提供，须作为假设或缺项说明。不能把两个暂停状态混为一个。
- I：提款专用暂停时，不应完成提款；这是流程约束，不要求正常时任何提款一定成功。可表示 `withdrawal_paused => !withdrawal_finalized`，限定有效确认场景。
- V：暂停时仍完成确认和提款；确认/资产转出可分开，不能只说缺 modifier。
- 语气：紧急事件是举例，资金抽干为 could/potential；不能升级为已发生或所有资产必被盗。

## sukuk_authority：错误检查 self allowance

原文明确：caller != owner；active owner 有 self allowance；未正确检查 owner 给 caller 的授权，owner 股份可烧毁，资产转给攻击者 receiver。

- P：caller 与 owner 不同、caller 没有足额授权、owner 有足额 self allowance、receiver 为攻击者；股份数量/余额等正常有效条件不明，应说明或限定。没有 caller 授权是从未经授权的攻击场景推导的条件。
- I：未经 owner 授权的第三方不得花费 owner 股份；可用 owner before/after 股份及授权金额，或特定未授权烧毁执行观察量表达，不用独立的“权限安全=true”。
- V：受害者股份烧毁并且资产发送给攻击者；只编码烧毁是部分效果，不能称完整盗窃。
- 语气：报告说直接盗窃，但依赖活跃受害者 self allowance 和有效余额等条件。不能去掉这些条件变成任何账户必被盗。

## merkl_callback：累计金额与实际转账金额

原文明确：callback 接收 cumulative amount 而非 toSend；第一次 claim 后二者会不同。

- P：存在先前 claim、本次累计权益与实际转账不同；金额和检查点必须属于同一次 claim、同一奖励币。实际数值计算式未提供，不虚构精确乘除关系。
- I：onClaim 的金额应等于实际转出金额，即 `callback_amount == transferred_amount`。
- V：callback_amount 等于累计权益、且不等于实际转账；不能只标“accounting error”。
- 语气：下游 desync/distribution/fund loss 是 can cause，不是必然已发生。可暂缓，必须列出限制。

## hybra_maturity：存款后冷却时间

原文明确：deposit 应设置 maturityTime=deposit timestamp+lockPeriod，withdraw 应等到成熟；实际 maturity mapping 没有写入、默认为零，用户可提前退出。

- P：有效存款、有正冷却期，在 deposit_time <= withdraw_time < deposit_time+lock_period 时尝试提款；使用这些业务条件须明确是限定场景。不能把实际零 maturity 当成应有 deadline。
- I：应设置 maturity_after_deposit == deposit_time+lock_period，或限定未成熟场景下 !withdrawal_completed；二者关注不同检查点，按声明范围核对，不强称全局等价。
- V：成熟时间未写入/为零、并且未到应有成熟时间仍退出。只编码 mapping 未写入或只编码收益变化，均不代表完整核心提款效果。
- 语气：reward siphoning、LP/trading/bribe 影响依赖其他机制，不直接用单次提前提款证明全部经济主张；不以这些复杂影响作已确认标准公式。

## gte_zero_cost：位运算导致误回退

原文明确：两笔正的 trade amount 可因 bitwise AND=0 被误判，比如 8 和 16；某些合法交易因此回退。

- P：两个交易金额都正、交易其余条件有效；若公式后端不支持 bitwise，可明确限定原文 8/16 样例并标范围部分覆盖，不能虚构完整 bitwise AST。
- I：双方支付都为正时，不应因零成本检测而回退；不是“任何正金额交易绝不回退”。
- V：合法非零金额交易因该检测误回退；根因 bitwise 与效果拒绝需要分开。数学 8&16=0 本身不等于调用已回退。
- 语气：重复 DoS/恶意利用是 potential；未表述资金被盗，不添加经济损失确定结论。
