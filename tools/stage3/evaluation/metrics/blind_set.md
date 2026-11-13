# 盲测样本集（跨项目）

- 样本数：40
- 抽取口径：扩样队列中的 judge-valid finding，排除当前 20 个 dev 项目，每项目最多 5 个
- PoC 骨架仍需 `tools/sol_resurrect_tool` 重建后才能进阶段三（P5 已知瓶颈）

| project | case | severity | title |
| --- | --- | --- | --- |
| SecondSwap_QERtzRkYcLK | SecondSwap_QERtzRkYcLK__1 | high | Rounding Issue in Price Calculation (Vesting Token) |
| SecondSwap_QERtzRkYcLK | SecondSwap_QERtzRkYcLK__1002 | high | Token issuer referral reward manipulation through combined direct and market Transfers |
| SecondSwap_QERtzRkYcLK | SecondSwap_QERtzRkYcLK__1010 | high | Arbitrary vesting transfer with other token issuers' tokens |
| SecondSwap_QERtzRkYcLK | SecondSwap_QERtzRkYcLK__1012 | high | Error in release rate calculation in StepVesting contract |
| SecondSwap_QERtzRkYcLK | SecondSwap_QERtzRkYcLK__1017 | high | `transferVesting` function is incorrectly implemented |
| Liquid_Ron_C7vLJT2ME8Z | Liquid_Ron_C7vLJT2ME8Z__1000 | high | Incorrect Operator Validation Allows Unauthorized Access While Blocking Operators |
| Liquid_Ron_C7vLJT2ME8Z | Liquid_Ron_C7vLJT2ME8Z__1027 | high | Operator assign the rewards to the operatorFeeAmount, although the funds are not still present in the contract |
| Liquid_Ron_C7vLJT2ME8Z | Liquid_Ron_C7vLJT2ME8Z__1032 | high | Opposite condition in `LiquidRon::onlyOperator` modifier allows anyone and prevents only operators instead of allowing only operators. |
| Liquid_Ron_C7vLJT2ME8Z | Liquid_Ron_C7vLJT2ME8Z__1036 | high | Due to operator fee also getting considered in share/asset calculation at withdraw/redeem after harvest is called users/attacker can exploit and withdraw more amount then they should as compared to someone who withdraws after Operator Fee is withdrawn |
| Liquid_Ron_C7vLJT2ME8Z | Liquid_Ron_C7vLJT2ME8Z__104 | high | Unintended reverts happen when any operator calls a function with the onlyOperator modifier |
| Megapot_SNxXumh3KqH | Megapot_SNxXumh3KqH__258 | high | Protocol Permanently Frozen via O(N) Gas DoS in Settlement - All Funds Locked at $10M Prize Pool |
| Megapot_SNxXumh3KqH | Megapot_SNxXumh3KqH__1004 | high | Payout calculator replacement permanently bricks historical claims |
| Megapot_SNxXumh3KqH | Megapot_SNxXumh3KqH__1021 | high | Settlement can be (re)triggered during emergency mode by attcker to selectively refund losing id and claim winning ones |
| Megapot_SNxXumh3KqH | Megapot_SNxXumh3KqH__1023 | high | Missing Check in setPayoutCalculator Causes Complete Loss of User Winnings |
| Megapot_SNxXumh3KqH | Megapot_SNxXumh3KqH__1032 | high | Mid-Drawing Parameter Manipulation: Owner Can Violate Core Invariants by Changing Active Drawing Parameters |
| Lambo.win_LVoZUeMUNkB | Lambo.win_LVoZUeMUNkB__102 | high | The `cashIn` Function won't be able to mint Tokens if the underlyingToken address is an ERC20 |
| Lambo.win_LVoZUeMUNkB | Lambo.win_LVoZUeMUNkB__105 | high | VirtualToken.cashIn incorrectly works with ERC20 tokens |
| Lambo.win_LVoZUeMUNkB | Lambo.win_LVoZUeMUNkB__109 | high | LamboFactory can be permanently DoS-ed due to createPair call reversal |
| Lambo.win_LVoZUeMUNkB | Lambo.win_LVoZUeMUNkB__118 | high | Incorrect Minting in cashIn() Function for Virtual Tokens Results in Permanent Loss of Initial Assets |
| Lambo.win_LVoZUeMUNkB | Lambo.win_LVoZUeMUNkB__119 | high | Incorrect token minting in `VirtualToken::cashIn` due to `msg.value` usage |
| THORWallet_PjDaAkTkN2w | THORWallet_PjDaAkTkN2w__175 | high | User can send `Titn` tokens to another address using bridge |
| THORWallet_PjDaAkTkN2w | THORWallet_PjDaAkTkN2w__460 | high | A user can easily restrict transfers for everyone except owner() on Base chain  |
| THORWallet_PjDaAkTkN2w | THORWallet_PjDaAkTkN2w__603 | high | Underflow Vulnerability in `withdrawRemainingTitn` Function |
| THORWallet_PjDaAkTkN2w | THORWallet_PjDaAkTkN2w__243 | medium | Permanent Bridged Token Holder Status has unintended issue |
| THORWallet_PjDaAkTkN2w | THORWallet_PjDaAkTkN2w__526 | medium | Cross-Chain Bridge Enables Transfer Restriction Evasion |
| Flare_-_FAsset_ZyMJvv6cLLi | Flare_-_FAsset_ZyMJvv6cLLi__288 | medium | Fixed challenge reward setter mixes NAT wei with USD5, mispricing challenger payouts |
| Flare_-_FAsset_ZyMJvv6cLLi | Flare_-_FAsset_ZyMJvv6cLLi__337 | medium | Integer division by `Conversion.GWEI (1e9)` in `executor fee` calculation causes precision loss in `CollateralReservationsFacet::reserveCollateral()` |
| Flare_-_FAsset_ZyMJvv6cLLi | Flare_-_FAsset_ZyMJvv6cLLi__104 | high | `redeem()` accepts `_lots` == 0 and can silently trap `msg.value` |
| Flare_-_FAsset_ZyMJvv6cLLi | Flare_-_FAsset_ZyMJvv6cLLi__129 | high | executeMinting lacks notEmergencyPaused allowing minting during pause |
| Flare_-_FAsset_ZyMJvv6cLLi | Flare_-_FAsset_ZyMJvv6cLLi__141 | high | Liquidation may use an incorrect amgToTokenWeiPrice when liquidating an agent’s position |
| Sequence_jEtbuty6H23 | Sequence_jEtbuty6H23__115 | high | `SessionManager::recoverSapientSignature` `permissionIdx` Can Be Hijack Which Allows Authorization Bypass Through Post-Signature Manipulation |
| Sequence_jEtbuty6H23 | Sequence_jEtbuty6H23__144 | high | `SessionSig::hashCallWithReplayProtection` Does Not Bind Signatures to Wallet Address, Enabling Cross-Wallet Replay Attacks |
| Sequence_jEtbuty6H23 | Sequence_jEtbuty6H23__160 | high | Relayer can escalate privileges by swapping unsigned call flag |
| Sequence_jEtbuty6H23 | Sequence_jEtbuty6H23__169 | high | Partial signature replay/frontrunning attack on session calls |
| Sequence_jEtbuty6H23 | Sequence_jEtbuty6H23__18 | high | `recoverSapientSignature` Returns Incorrect Value, Breaking Sapient Signer Functionality |
| Silo_Finance_yjrYyfyTzWc | Silo_Finance_yjrYyfyTzWc__444 | high | Inaccurate calculation of `toSupply` provided to a market may result in reduced supply allocation for certain markets. |
| Silo_Finance_yjrYyfyTzWc | Silo_Finance_yjrYyfyTzWc__446 | high | Non-compliance with ERC4626 Standard due to Incorrect `decimals()` Return Value |
| Silo_Finance_yjrYyfyTzWc | Silo_Finance_yjrYyfyTzWc__453 | high | The discrepancy between how shares and deposits are valued can be exploited to drain SiloVault |
| Silo_Finance_yjrYyfyTzWc | Silo_Finance_yjrYyfyTzWc__454 | high | Deflation attack |
| Silo_Finance_yjrYyfyTzWc | Silo_Finance_yjrYyfyTzWc__468 | high | SiloVault::maxDeposit & maxMint are not compliant with ERC4626 |
