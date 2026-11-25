# 主口径执行 backlog（可重放、无 LLM/forge）

- 正样本：`mainline_sample_mini.json`，共 `40` 例。
- 各桶数量之和 = 正样本总数。

| 桶 | 数量 | 下一步动作 |
| --- | ---: | --- |
| done | 4 | 无需动作 |
| rebind | 6 | `stage3_verdict_loop` 重提绑定 |
| stage2_rerun | 1 | 修 stage2 弱不变量后重跑 |
| reference_patch | 3 | 提供 M1 参考补丁 |
| other | 21 | 逐例人工归因 |
| stage3_ready | 3 | 跑 stage3（`run_mainline_stage3_consumer.py`） |
| stage2_retry_402 | 0 | 修计费后重跑 stage2 |
| stage2_real_fail | 2 | 修 stage2 形式化 |

## stage2 真失败分布

| 根因 | 数量 |
| --- | ---: |
| core_piv_not_fully_formalized | 1 |
| needs_review | 1 |

## rebind 队列

| case | verdict |
| --- | --- |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__QW9maHr29yd__sRR6R7uhY36 | partial_binding |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__KYKEdg3wHRs | compile_error |
| Hybra_Finance_xo4hapwL2Jy__7LKTwwSAteH__oX4gqWn5JPV | binding_error |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__uaBoVFLvr85 | binding_error |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__YFfbDGPYnUz | binding_error |
| Brix_Money_qy7NXr77sDh__Nxh87eHBt9G__hX7p7s459Aw | partial_binding |

## stage2_rerun（弱不变量）

| case | verdict |
| --- | --- |
| Hybra_Finance_xo4hapwL2Jy__PzD5FbkNA5e__YAoPVKDcekp | effect_observed_invariant_holds |

## reference_patch（机制天花板）

| case | verdict |
| --- | --- |
| Merkl_T4ExvutBBXC__9JnmzBSjjfp__SuKXTvLqrK5 | not_dynamically_expressible |
| Ekubo_3FTodhsvBkM__dtK3s8JSnTx__QCyardr6BSH | not_dynamically_expressible |
| Covenant_d4uY8y2AMSs__zTAab6iGGZx__Dxst84uDVNZ | reference_patch_required |
