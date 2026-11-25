# 盲测 PoC 骨架构建状态

阶段一优先使用 `blind_flatten_root` 的正式 flatten 产物；`sol_resurrect` 仅作为骨架回退。

盲测样本 **40**；已重建 **40**；编译通过 **26**；有 test entrypoint **10**；正式 flatten 就绪 **10**。

| case | project | 状态 | 阶段一路径 | forge | 失败类 | test entrypoint |
| --- | --- | --- | --- | --- | --- | --- |
| SecondSwap_QERtzRkYcLK__1 | SecondSwap_QERtzRkYcLK | built | sol_resurrect | ok | - | False |
| SecondSwap_QERtzRkYcLK__1002 | SecondSwap_QERtzRkYcLK | built | sol_resurrect | ok | - | False |
| SecondSwap_QERtzRkYcLK__1010 | SecondSwap_QERtzRkYcLK | built | sol_resurrect | ok | - | False |
| SecondSwap_QERtzRkYcLK__1012 | SecondSwap_QERtzRkYcLK | built | sol_resurrect | ok | - | False |
| SecondSwap_QERtzRkYcLK__1017 | SecondSwap_QERtzRkYcLK | built | sol_resurrect | ok | - | False |
| Liquid_Ron_C7vLJT2ME8Z__1000 | Liquid_Ron_C7vLJT2ME8Z | built | flatten_root | ok | - | True |
| Liquid_Ron_C7vLJT2ME8Z__1027 | Liquid_Ron_C7vLJT2ME8Z | built | flatten_root | ok | - | True |
| Liquid_Ron_C7vLJT2ME8Z__1032 | Liquid_Ron_C7vLJT2ME8Z | built | flatten_root | ok | - | True |
| Liquid_Ron_C7vLJT2ME8Z__1036 | Liquid_Ron_C7vLJT2ME8Z | built | flatten_root | ok | - | True |
| Liquid_Ron_C7vLJT2ME8Z__104 | Liquid_Ron_C7vLJT2ME8Z | built | flatten_root | ok | - | True |
| Megapot_SNxXumh3KqH__258 | Megapot_SNxXumh3KqH | built | sol_resurrect | ok | - | False |
| Megapot_SNxXumh3KqH__1004 | Megapot_SNxXumh3KqH | built | sol_resurrect | failed | missing_symbol | False |
| Megapot_SNxXumh3KqH__1021 | Megapot_SNxXumh3KqH | built | sol_resurrect | failed | missing_symbol | False |
| Megapot_SNxXumh3KqH__1023 | Megapot_SNxXumh3KqH | built | sol_resurrect | failed | missing_symbol | False |
| Megapot_SNxXumh3KqH__1032 | Megapot_SNxXumh3KqH | built | sol_resurrect | failed | missing_symbol | False |
| Lambo.win_LVoZUeMUNkB__102 | Lambo.win_LVoZUeMUNkB | built | flatten_root | ok | - | True |
| Lambo.win_LVoZUeMUNkB__105 | Lambo.win_LVoZUeMUNkB | built | flatten_root | ok | - | True |
| Lambo.win_LVoZUeMUNkB__109 | Lambo.win_LVoZUeMUNkB | built | sol_resurrect | ok | - | False |
| Lambo.win_LVoZUeMUNkB__118 | Lambo.win_LVoZUeMUNkB | built | sol_resurrect | ok | - | False |
| Lambo.win_LVoZUeMUNkB__119 | Lambo.win_LVoZUeMUNkB | built | flatten_root | ok | - | True |
| THORWallet_PjDaAkTkN2w__175 | THORWallet_PjDaAkTkN2w | built | sol_resurrect | failed | missing_symbol | False |
| THORWallet_PjDaAkTkN2w__460 | THORWallet_PjDaAkTkN2w | built | sol_resurrect | failed | missing_symbol | False |
| THORWallet_PjDaAkTkN2w__603 | THORWallet_PjDaAkTkN2w | built | sol_resurrect | ok | - | False |
| THORWallet_PjDaAkTkN2w__243 | THORWallet_PjDaAkTkN2w | built | sol_resurrect | failed | missing_symbol | False |
| THORWallet_PjDaAkTkN2w__526 | THORWallet_PjDaAkTkN2w | built | sol_resurrect | failed | missing_symbol | False |
| Flare_-_FAsset_ZyMJvv6cLLi__288 | Flare_-_FAsset_ZyMJvv6cLLi | built | sol_resurrect | ok | - | False |
| Flare_-_FAsset_ZyMJvv6cLLi__337 | Flare_-_FAsset_ZyMJvv6cLLi | built | sol_resurrect | ok | - | False |
| Flare_-_FAsset_ZyMJvv6cLLi__104 | Flare_-_FAsset_ZyMJvv6cLLi | built | sol_resurrect | failed | other | False |
| Flare_-_FAsset_ZyMJvv6cLLi__129 | Flare_-_FAsset_ZyMJvv6cLLi | built | sol_resurrect | failed | missing_symbol | False |
| Flare_-_FAsset_ZyMJvv6cLLi__141 | Flare_-_FAsset_ZyMJvv6cLLi | built | sol_resurrect | failed | missing_symbol | False |
| Sequence_jEtbuty6H23__115 | Sequence_jEtbuty6H23 | built | sol_resurrect | ok | - | False |
| Sequence_jEtbuty6H23__144 | Sequence_jEtbuty6H23 | built | sol_resurrect | ok | - | False |
| Sequence_jEtbuty6H23__160 | Sequence_jEtbuty6H23 | built | sol_resurrect | ok | - | False |
| Sequence_jEtbuty6H23__169 | Sequence_jEtbuty6H23 | built | sol_resurrect | ok | - | False |
| Sequence_jEtbuty6H23__18 | Sequence_jEtbuty6H23 | built | sol_resurrect | ok | - | False |
| Silo_Finance_yjrYyfyTzWc__444 | Silo_Finance_yjrYyfyTzWc | built | sol_resurrect | failed | other | False |
| Silo_Finance_yjrYyfyTzWc__446 | Silo_Finance_yjrYyfyTzWc | built | flatten_root | ok | - | True |
| Silo_Finance_yjrYyfyTzWc__453 | Silo_Finance_yjrYyfyTzWc | built | flatten_root | ok | - | True |
| Silo_Finance_yjrYyfyTzWc__454 | Silo_Finance_yjrYyfyTzWc | built | sol_resurrect | failed | other | False |
| Silo_Finance_yjrYyfyTzWc__468 | Silo_Finance_yjrYyfyTzWc | built | sol_resurrect | failed | other | False |
