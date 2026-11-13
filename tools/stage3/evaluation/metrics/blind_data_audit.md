# 盲测数据就绪审计

样本 **40**；submission 在本地 **40**；含 PoC 代码块 **35**；合约骨架可编译 **10**；完全就绪 **0**。

| case | project | submission | PoC 块 | PoC 动作 | 骨架编译 | blockers |
| --- | --- | ---: | ---: | --- | --- | --- |
| SecondSwap_QERtzRkYcLK__1 | SecondSwap_QERtzRkYcLK | Y | 0 | no_poc_code | ok | no_poc_code_block, no_test_entrypoint_in_harness |
| SecondSwap_QERtzRkYcLK__1002 | SecondSwap_QERtzRkYcLK | Y | 2 | snippet_only | ok | poc_is_snippet_not_harness, no_test_entrypoint_in_harness |
| SecondSwap_QERtzRkYcLK__1010 | SecondSwap_QERtzRkYcLK | Y | 4 | snippet_only | ok | poc_is_snippet_not_harness, no_test_entrypoint_in_harness |
| SecondSwap_QERtzRkYcLK__1012 | SecondSwap_QERtzRkYcLK | Y | 2 | snippet_only | ok | poc_is_snippet_not_harness, no_test_entrypoint_in_harness |
| SecondSwap_QERtzRkYcLK__1017 | SecondSwap_QERtzRkYcLK | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Liquid_Ron_C7vLJT2ME8Z__1000 | Liquid_Ron_C7vLJT2ME8Z | Y | 1 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Liquid_Ron_C7vLJT2ME8Z__1027 | Liquid_Ron_C7vLJT2ME8Z | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Liquid_Ron_C7vLJT2ME8Z__1032 | Liquid_Ron_C7vLJT2ME8Z | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Liquid_Ron_C7vLJT2ME8Z__1036 | Liquid_Ron_C7vLJT2ME8Z | Y | 1 | bare_test_fn | pending_resurrection | contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Liquid_Ron_C7vLJT2ME8Z__104 | Liquid_Ron_C7vLJT2ME8Z | Y | 6 | bare_test_fn | pending_resurrection | contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Megapot_SNxXumh3KqH__258 | Megapot_SNxXumh3KqH | Y | 5 | snippet_only | ok | poc_is_snippet_not_harness, no_test_entrypoint_in_harness |
| Megapot_SNxXumh3KqH__1004 | Megapot_SNxXumh3KqH | Y | 0 | no_poc_code | pending_resurrection | no_poc_code_block, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Megapot_SNxXumh3KqH__1021 | Megapot_SNxXumh3KqH | Y | 4 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Megapot_SNxXumh3KqH__1023 | Megapot_SNxXumh3KqH | Y | 9 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Megapot_SNxXumh3KqH__1032 | Megapot_SNxXumh3KqH | Y | 3 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Lambo.win_LVoZUeMUNkB__102 | Lambo.win_LVoZUeMUNkB | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Lambo.win_LVoZUeMUNkB__105 | Lambo.win_LVoZUeMUNkB | Y | 2 | snippet_only | ok | poc_is_snippet_not_harness, no_test_entrypoint_in_harness |
| Lambo.win_LVoZUeMUNkB__109 | Lambo.win_LVoZUeMUNkB | Y | 2 | snippet_only | failed | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Lambo.win_LVoZUeMUNkB__118 | Lambo.win_LVoZUeMUNkB | Y | 2 | fork_rpc | pending_resurrection | poc_forks_live_rpc, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Lambo.win_LVoZUeMUNkB__119 | Lambo.win_LVoZUeMUNkB | Y | 3 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| THORWallet_PjDaAkTkN2w__175 | THORWallet_PjDaAkTkN2w | Y | 1 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| THORWallet_PjDaAkTkN2w__460 | THORWallet_PjDaAkTkN2w | Y | 1 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| THORWallet_PjDaAkTkN2w__603 | THORWallet_PjDaAkTkN2w | Y | 3 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| THORWallet_PjDaAkTkN2w__243 | THORWallet_PjDaAkTkN2w | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| THORWallet_PjDaAkTkN2w__526 | THORWallet_PjDaAkTkN2w | Y | 0 | no_poc_code | failed | no_poc_code_block, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Flare_-_FAsset_ZyMJvv6cLLi__288 | Flare_-_FAsset_ZyMJvv6cLLi | Y | 0 | no_poc_code | ok | no_poc_code_block, no_test_entrypoint_in_harness |
| Flare_-_FAsset_ZyMJvv6cLLi__337 | Flare_-_FAsset_ZyMJvv6cLLi | Y | 10 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Flare_-_FAsset_ZyMJvv6cLLi__104 | Flare_-_FAsset_ZyMJvv6cLLi | Y | 4 | repo_test_deps | pending_resurrection | contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Flare_-_FAsset_ZyMJvv6cLLi__129 | Flare_-_FAsset_ZyMJvv6cLLi | Y | 1 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Flare_-_FAsset_ZyMJvv6cLLi__141 | Flare_-_FAsset_ZyMJvv6cLLi | Y | 3 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Sequence_jEtbuty6H23__115 | Sequence_jEtbuty6H23 | Y | 7 | bare_test_fn | pending_resurrection | contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Sequence_jEtbuty6H23__144 | Sequence_jEtbuty6H23 | Y | 4 | fork_rpc | ok | poc_forks_live_rpc, no_test_entrypoint_in_harness |
| Sequence_jEtbuty6H23__160 | Sequence_jEtbuty6H23 | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Sequence_jEtbuty6H23__169 | Sequence_jEtbuty6H23 | Y | 4 | fork_rpc | ok | poc_forks_live_rpc, no_test_entrypoint_in_harness |
| Sequence_jEtbuty6H23__18 | Sequence_jEtbuty6H23 | Y | 2 | fork_rpc | ok | poc_forks_live_rpc, no_test_entrypoint_in_harness |
| Silo_Finance_yjrYyfyTzWc__444 | Silo_Finance_yjrYyfyTzWc | Y | 2 | snippet_only | failed | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Silo_Finance_yjrYyfyTzWc__446 | Silo_Finance_yjrYyfyTzWc | Y | 4 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Silo_Finance_yjrYyfyTzWc__453 | Silo_Finance_yjrYyfyTzWc | Y | 10 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Silo_Finance_yjrYyfyTzWc__454 | Silo_Finance_yjrYyfyTzWc | Y | 0 | no_poc_code | failed | no_poc_code_block, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
| Silo_Finance_yjrYyfyTzWc__468 | Silo_Finance_yjrYyfyTzWc | Y | 2 | snippet_only | pending_resurrection | poc_is_snippet_not_harness, contract_skeleton_not_compiling, no_test_entrypoint_in_harness |
