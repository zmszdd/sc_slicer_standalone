# Revert-witness effect policy re-audit

> Read-only.  Authoritative metrics are not rewritten by this audit.

- applied candidates: **13**
- policy-eligible: **6**
- metric-eligible candidates: **5**
- eligible cases (TP projection): **2**
- raw TP before policy: 5
- TP already adjudicated in metrics: 2
- projected TP: 7 (matches integrated metrics: True)
- recall: 14.3% -> 20.0%
- accuracy: 14.3% -> 20.0%

| case | claim | impact | metric eligible | policy | reason |
| --- | --- | --- | --- | --- | --- |
| Hybra_Finance_xo4hapwL2Jy__XgPnfi6S3qh__K5hvaZWagxN | `impact_claim_functional_dos_full_exit_wi_49307db0_c15a2bfa` | `dust_or_donation_dos` | no | eligible | `revert_is_vulnerable_operation` |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__VcuomLx35E9 | `impact_claim_permanent_asset_theft_64cbd058_daf0a8ec` | `direct_fund_loss` | yes | eligible | `revert_is_vulnerable_operation` |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__VcuomLx35E9 | `impact_claim_direct_loss_of_user_funds_0f24b839_daf0a8ec` | `other_or_unknown` | yes | eligible | `revert_is_vulnerable_operation` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__qFXS4TWRDTc__dHyYZoKzTEW | `impact_claim_per_pool_permanent_dos_quot_6d415b59_041a2a67` | `dust_or_donation_dos` | no | rejected | `revert_not_vulnerable_operation` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__qFXS4TWRDTc__dHyYZoKzTEW | `impact_claim_per_pool_permanent_dos_quot_6d415b59_ecad2797` | `dust_or_donation_dos` | no | rejected | `revert_not_vulnerable_operation` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__i74QjxE4Y98 | `impact_claim_base_512_quote_1_511_revert_5a1c1edf_9a667fbf` | `other_or_unknown` | yes | eligible | `revert_is_vulnerable_operation` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__i74QjxE4Y98 | `impact_claim_base_256_quote_1_255_revert_879ef8f1_e35a45f2` | `other_or_unknown` | yes | eligible | `revert_is_vulnerable_operation` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__i74QjxE4Y98 | `impact_claim_base_1024_quote_1_1023_reve_8e8381de_e35a45f2` | `other_or_unknown` | yes | eligible | `revert_is_vulnerable_operation` |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__5gEysuN9QMh | `impact_claim_all_natural_expiry_locks_af_788e4c01_eb1de04a` | `other_or_unknown` | yes | rejected | `revert_not_vulnerable_operation` |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__ScVqnBqSyyG | `impact_claim_admin_cannot_halt_batch_ope_d28f0dcf_9df2f9e3` | `other_or_unknown` | yes | rejected | `revert_not_vulnerable_operation` |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__ScVqnBqSyyG | `impact_claim_validator_continue_processi_9a2a6dc8_96feaf56` | `other_or_unknown` | yes | rejected | `revert_not_vulnerable_operation` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__LPhijqJeGx2__iikf7iAzHKQ | `impact_claim_ineffective_emergency_respo_f653ade5_ba796262` | `other_or_unknown` | yes | rejected | `revert_not_vulnerable_operation` |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__TLnoWTYjws5 | `impact_claim_direct_theft_accumulated_bu_1d1ff616_d3b3945c` | `direct_fund_loss` | yes | rejected | `revert_not_vulnerable_operation` |

Next: The metric layer now integrates this report-only policy.  Moving the same adjudication into execution requires a PROTOCOL_VERSION bump and rerun.
