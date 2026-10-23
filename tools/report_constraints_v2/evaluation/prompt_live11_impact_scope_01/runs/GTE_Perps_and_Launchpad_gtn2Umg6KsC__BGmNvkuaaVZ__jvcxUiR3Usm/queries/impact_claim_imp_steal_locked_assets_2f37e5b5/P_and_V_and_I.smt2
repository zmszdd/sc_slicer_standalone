; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca952c8d1_accrued_launchpad_fees_present () Bool)
(declare-fun ca952c8d1_caller_has_no_special_permissions () Bool)
(declare-fun ca952c8d1_locked_assets_stolen () Bool)
(declare-fun ca952c8d1_no_token_transfers_in_call () Bool)
(declare-fun ca952c8d1_rewards_accrual_enabled () Bool)
(assert
 (= ca952c8d1_accrued_launchpad_fees_present ca952c8d1_accrued_launchpad_fees_present))
(assert
 (= ca952c8d1_caller_has_no_special_permissions ca952c8d1_caller_has_no_special_permissions))
(assert
 (= ca952c8d1_locked_assets_stolen ca952c8d1_locked_assets_stolen))
(assert
 (= ca952c8d1_no_token_transfers_in_call ca952c8d1_no_token_transfers_in_call))
(assert
 (= ca952c8d1_rewards_accrual_enabled ca952c8d1_rewards_accrual_enabled))
(define-fun report_preconditions () Bool (and ca952c8d1_rewards_accrual_enabled
     ca952c8d1_accrued_launchpad_fees_present
     ca952c8d1_no_token_transfers_in_call
     ca952c8d1_caller_has_no_special_permissions))
(define-fun report_safety () Bool (=> (and ca952c8d1_rewards_accrual_enabled
         ca952c8d1_accrued_launchpad_fees_present
         ca952c8d1_no_token_transfers_in_call
         ca952c8d1_caller_has_no_special_permissions)
    (not ca952c8d1_locked_assets_stolen)))
(define-fun report_effects () Bool (and ca952c8d1_rewards_accrual_enabled
     ca952c8d1_accrued_launchpad_fees_present
     ca952c8d1_no_token_transfers_in_call
     ca952c8d1_caller_has_no_special_permissions
     (not (not ca952c8d1_locked_assets_stolen))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
