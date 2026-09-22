# semantic-v3 留出集预先参考

状态：`assistant_preliminary_reference`，尚未经用户或独立专家审核。日期：2026-09-15。本文件在真实模型调用前仅依据报告描述和影响整理，不读取 PoC、不读取本批模型输出，也不发送给模型。

冻结 Prompt：`semantic-v3`；`semantic_prompts.py` SHA-256：`c91a8ea3bc206420deb22827fbdd6d9a5c368142f3448d9ded8186c9e814709b`。

五份来自不同项目和 finding，未参与 semantic-v3 的规则或示例设计，也不在 multi_report_01 开发评测中。它们是定向选择的短报告，不是随机总体样本。评估报告声称的语义，不认证漏洞实现真实性。

## 固定评分

沿用六维：范围/主体、核心 P、安全意图、I 公式对应、核心 V、范围/语气与未覆盖影响。取值 pass/partial/fail/not_evaluable；partial 不算完整正确，失败输出不移出分母。另统计证据/结构通过、正式链路完成和 candidate_checks_passed，但它们不等于语义准确率。

核心 I 的 pass 必须同时满足：语义方向、执行限定、文字/AST、观察量和当前类型/算子兼容；公式等价即可，不按变量名匹配。若报告核心依赖当前 AST 不支持的运算，正确弃权为 not_evaluable，不算 fail，也不算 pass；不得用无定义布尔量冒充。

### upside_dust_fee

- 范围：processSwapFee 对小额 swap 计算 basis-point fee；用户可重复拆成 dust swap，协议或 fee recipient 少收费用。
- P：token amount 与 swapFeeBp 均为正，且 product 小于 10,000；重复操作只属于更广影响。乘法当前 AST 不支持，不能把 `product_below_divisor` 自由布尔量当完整数值定义。
- I：在报告所述“非零 fee intended”的收费场景，不能因整数除法把应收 swap fee 计算为零。允许表达为限定 P 下 `charged_fee > 0`；若不能忠实表达 P，应将公式 null/unresolved，而不是声称任意正 amount/rate 都必然收费。
- V：报告声称 charged fee 为零；持续/总体预期收入损失是更广影响。
- 模态：零费能力为 asserted；反复拆单为 can，规模与实际损失未量化。

### virtuals_update_impact

- 范围：ServiceNft.updateImpact 修改 `_impacts` 与 `_maturities`；任意外部地址可调用。
- P：caller 未获授权并尝试/成功调用 updateImpact；报告未提供具体授权角色名称，不能强造 owner/admin 身份。
- I：未经授权的调用不得成功修改这些关键状态。可表达 `update_completed => caller_authorized`，或 `!caller_authorized => impacts_after==before && maturities_after==before`。
- V：未经授权者成功修改 impact/maturity；只表达“函数缺 modifier”是根因而非 V。
- 模态：状态可被任意地址篡改是作者声称的能力；不公平奖励和系统操纵是 could/potential，不得升级为既成损失。

### morpheus_past_lock

- 范围：首次 `_stake` 设置 claimLockEnd；攻击者提供过去的非零时间戳，使奖励立即可领取。
- P：首次 stake、现有 userData.claimLockEnd=0，输入 claimLockEnd_ 为正但小于/equal 当前时间，且通过报告给出的比较；小额 stake 等其他有效条件未给出则说明。
- I：成功建立需要锁定的 stake 后，奖励在未来有效锁到期前不可领取；可表达 `stake_completed && supplied_lock_end <= now => !rewards_immediately_accessible`，或要求成功设置的有效 lock end 在未来。不能要求任何调用输入天然在未来。
- V：过去时间戳被接受且奖励立即可访问，构成 lock bypass。
- 模态：作者明确声称 bypass 能力；相对正常用户的不公平是影响，未量化资金损失。

### forte_le_equal

- 范围：Float128.le 比较两个数值相等但 packed/mantissa 表示不同的输入，其中涉及 L Mantissa；返回 false。
- P：两输入数值语义相等，且进入报告描述的 mantissa 路径。packed 位级解码当前 AST 不支持，可用同单位 decoded numeric observations；无法定义相等关系则弃权。
- I：若两个被比较数值相等，less-than-or-equal 结果必须为 true，即 `numeric_a==numeric_b => le_result`，限定 le 调用。
- V：技术上相等的两个 packed float 得到 le=false。不得把 packed bits 相等误作数值相等；报告说同种 mantissa 表示会被早期 equality 检查遮蔽。
- 模态：核心返回错误 asserted；更广调用方损失未报告，不添加。

### covenant_self_transfer

- 范围：redeem 或 DEBT→BASE swap 指定 `to=Covenant`；ERC-20 self-transfer 不改 token balance，但内部 baseSupply 减少，后续 exact-out/withdraw 可能回退。
- P：to 为 Covenant 自身、BASE out amount>0、调用者持有足够 zToken/满足相应有效条件；无需治理角色。重复只属于持续影响。
- I：self-transfer 不应单独降低与实际库存对应的内部 supply；可表达 self-transfer 下 `base_supply_after==base_supply_before`，或保持 `base_supply==actual_balance` 的前后关系。
- V：actual BASE balance 不变而 baseSupply 降低，产生 mismatch；后续本可由真实余额覆盖但超过错误 baseSupply 的请求回退，是第二个有条件效果。
- 模态：单次 mismatch 及可执行攻击能力 asserted；可重复降到受 zToken budget 限制，持续 DoS 范围不能从单次状态完整证明。

## 防污染和解释边界

模型只接收编号原文；第二次接收第一步要素与编号片段。PoC、本文、旧 Prompt、开发集答案和历史模型输出均不发送。程序保存实际 prompt.txt 及哈希。人工评分必须在原始输出固定后另存；不能补公式再计模型成功。

semantic-v3 与旧 40% 基线使用不同报告，因此只能比较趋势，不能宣称严格 A/B 因果提升。若要严格比较，需以后在新的第三批报告上同时运行冻结旧版和 v3，并单独授权成本。
