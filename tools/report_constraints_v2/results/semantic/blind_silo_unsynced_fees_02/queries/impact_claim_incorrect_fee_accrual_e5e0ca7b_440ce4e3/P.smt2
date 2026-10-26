; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd60e8c9f_accrue_fee_called_before_claim () Bool)
(declare-fun cd60e8c9f_claim_rewards_invoked () Bool)
(declare-fun cd60e8c9f_fee_accrual_from_interest_occurs () Bool)
(declare-fun cd60e8c9f_incorrect_total_supply_used_for_fee_accrual () Bool)
(declare-fun cd60e8c9f_transfer_via_update_hook_occurs () Bool)
(assert
 (= cd60e8c9f_accrue_fee_called_before_claim cd60e8c9f_accrue_fee_called_before_claim))
(assert
 (= cd60e8c9f_claim_rewards_invoked cd60e8c9f_claim_rewards_invoked))
(assert
 (= cd60e8c9f_fee_accrual_from_interest_occurs cd60e8c9f_fee_accrual_from_interest_occurs))
(assert
 (= cd60e8c9f_incorrect_total_supply_used_for_fee_accrual cd60e8c9f_incorrect_total_supply_used_for_fee_accrual))
(assert
 (= cd60e8c9f_transfer_via_update_hook_occurs cd60e8c9f_transfer_via_update_hook_occurs))
(define-fun report_preconditions () Bool (and cd60e8c9f_transfer_via_update_hook_occurs
     cd60e8c9f_fee_accrual_from_interest_occurs))
(define-fun report_safety () Bool (=> cd60e8c9f_claim_rewards_invoked cd60e8c9f_accrue_fee_called_before_claim))
(define-fun report_effects () Bool cd60e8c9f_incorrect_total_supply_used_for_fee_accrual)
(assert report_preconditions)
(check-sat)
(get-model)
