# Negative label-review gate

- protocol: `mainline/1.7.36`
- cases requiring review: **2**

| case | claim | run |
| --- | --- | --- |
| `GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__MDvgv55V6yC` | `impact_claim_misleading_liquidity_inform_29ea384a_8e07b07e` | `GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__MDvgv55V6yC__impact_claim_misleading_liquidity_inform_29ea384a_8e07b07e__20261124T124508Z` |
| `Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__4DNu4EkJqs3` | `impact_claim_prevented_staking_below_lim_e18f5b5a_80f37a9d` | `Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__4DNu4EkJqs3__impact_claim_prevented_staking_below_lim_e18f5b5a_80f37a9d__20261123T144016Z` |

terminal current-protocol violation_reproduced on a frozen negative is a label-review signal; it is not converted to FP or TN and only blocks publication until adjudicated.
