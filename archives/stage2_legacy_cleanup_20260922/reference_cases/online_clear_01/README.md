# 公开真实报告 P/I/V 参考集 01

日期：2026-09-15。用途：从清晰的真实漏洞报告中提炼**逻辑构造方式**，改进阶段二 Prompt；不是阶段三 PoC 验证集。

## 边界

- 来源均为 Code4rena 已公开的 Findings & Analysis Report。
- 下列 P/I/V 是助手依据报告正文整理的候选参考，尚未经独立专家确认，因此状态为 `assistant_preliminary_reference`，不能称为人工金标准。
- Prompt 不接收项目名、报告答案或下面的公式；只吸收“权限、边界、顺序、状态变化”这些通用逻辑构造原则。
- 后续用这些案例调 Prompt 时，它们属于开发集，不能再作为 v3.2 的留出测试集。
- 这里只评价报告语义是否被忠实形式化，不评价漏洞是否能在真实代码中复现。

## 入选案例

### 1. PoolTogether：`rngComplete` 缺少访问控制

来源：[Code4rena PoolTogether H-02](https://code4rena.com/reports/2023-08-pooltogether#h-02-rngcomplete-function-should-only-be-called-by-rngauctionrelayer)

- P：调用者不是指定 relayer；其调用 `rngComplete`。
- I：若 RNG 完成并发放奖励，则调用者必须是指定 relayer。
- V：非 relayer 完成 RNG，并把奖励接收者设为自己控制的地址。
- 核心形式：`completed -> caller_is_relayer`；V 必须同时包含 `completed` 与 `not caller_is_relayer`。
- 学到的规则：不能只把“攻击者获得奖励”作为 V，否则可能无法在逻辑上否定访问控制 I。

### 2. Reality Cards：市场时间顺序未完整校验

来源：[Code4rena Reality Cards M-05](https://code4rena.com/reports/2021-06-realitycards#m-05-rcfactorycreatemarket-does-not-enforce-_timestamps1-and-_timestamps2-being-larger-than-_timestamps0-even-though-proper-functioning-requires-them-to-be-so)

- P：创建市场时，调用者提供 `locking_time <= opening_time` 的输入。
- I：市场创建成功意味着 `opening_time < locking_time`。
- V：市场在时间顺序非法时仍被创建。
- 核心形式：`market_created -> opening_time < locking_time`；V 为 `market_created and locking_time <= opening_time`。
- 学到的规则：非法输入关系属于调用前可观察条件；“创建成功”是结果，不能混进 P。

### 3. Reality Cards：可提交未来时间收租

来源：[Code4rena Reality Cards H-04](https://code4rena.com/reports/2021-06-realitycards#h-04-anyone-can-affect-deposits-of-any-user-and-turn-the-owner-of-the-token)

- P：调用者为目标用户提交晚于当前区块时间的 `_timeToCollectTo`。
- I：若收租结算完成，目标结算时间不得晚于当前区块时间。
- V：未来时间的收租结算仍完成，进而可把用户置为 foreclosed。
- 核心形式：`collection_completed -> requested_time <= current_time`；V 为 `collection_completed and requested_time > current_time`。
- 学到的规则：下游 foreclosure 是影响，核心 V 应先表达直接违反时间边界的完成事件。

### 4. Reality Cards：用户价格上限被突破

来源：[Code4rena Reality Cards M-07](https://code4rena.com/reports/2021-06-realitycards#m-07-maxsumofprices-check-is-broken)

- P：用户调用批量租赁并提供 `_maxSumOfPrices` 上限。
- I：批量租赁完成时，实际投标价格总和不得超过用户给定上限。
- V：批量租赁完成且实际总和大于上限。
- 核心形式：`completed -> actual_sum <= user_cap`；V 为 `completed and actual_sum > user_cap`。
- 学到的规则：必须保留 `<=` 的方向和用户给定值，不能弱化成“用户可能损失”。

### 5. Brix Money：受限用户通过跨链路径继续质押

来源：[Code4rena Brix Money M-01](https://code4rena.com/reports/2025-11-brix-money#m-01-user-can-bypass-staking-restrictions-through-composer-and-deposit-on-another-chain)

- P：用户已具有受限角色，并尝试通过跨链 composer 路径存入资产。
- I：受限用户的质押/铸造操作不得完成。
- V：受限用户经 composer 完成存入，并在另一条链收到相应 `wiTRY`。
- 核心形式：`stake_completed -> not user_restricted`；V 为 `stake_completed and user_restricted`。
- 学到的规则：检查中间合约地址不等于检查真实用户；P 必须保留“用户受限”和“跨链路径”。

## 未入选案例及原因

- Basin M-05：报告明确给出乘法不变量，但当前阶段二 AST 不支持乘法；可用于未来 DSL 扩展，不适合作为当前可执行标准。
- HydraDX 最小流动性：报告讨论中存在“硬不变量还是软保护”的争议，不适合低歧义参考。
- Reality Cards 全局暂停绕过：赞助方对 pause 的精确范围有异议，不作为标准答案。
- Drips 授权撤销抢跑：涉及多主体授权图和跨交易顺序，留到支持时序/关系建模后再纳入。

## 对 Prompt 的直接改进

这些案例共同支持四个不依赖项目名称的构造模块：

1. 权限：`sensitive_effect -> authorized`。
2. 上限或时间边界：`completed -> observed <= limit`。
3. 非法输入拒绝：`invalid_input -> not completed`。
4. 状态保护：`trigger -> state_after == state_before`。

V 必须用独立的可观察量明确表达对应反例，例如 `sensitive_effect and not authorized`，而不是只写模糊的经济损失。使用模块前仍必须从当前报告找到对应证据；不匹配时返回 unresolved，不能套模板猜答案。
