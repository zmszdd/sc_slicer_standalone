; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0100c166_accrued_fees_present () Bool)
(declare-fun c0100c166_caller_has_no_special_permissions () Bool)
(declare-fun c0100c166_fees_counted_as_user_supplied () Bool)
(declare-fun c0100c166_locked_assets_drained () Bool)
(declare-fun c0100c166_no_token_transfers_in () Bool)
(declare-fun c0100c166_rewards_accrual_enabled () Bool)
(assert
 (= c0100c166_accrued_fees_present c0100c166_accrued_fees_present))
(assert
 (= c0100c166_caller_has_no_special_permissions c0100c166_caller_has_no_special_permissions))
(assert
 (= c0100c166_fees_counted_as_user_supplied c0100c166_fees_counted_as_user_supplied))
(assert
 (= c0100c166_locked_assets_drained c0100c166_locked_assets_drained))
(assert
 (= c0100c166_no_token_transfers_in c0100c166_no_token_transfers_in))
(assert
 (= c0100c166_rewards_accrual_enabled c0100c166_rewards_accrual_enabled))
(define-fun report_preconditions () Bool (and c0100c166_rewards_accrual_enabled
     c0100c166_accrued_fees_present
     c0100c166_no_token_transfers_in
     c0100c166_caller_has_no_special_permissions))
(define-fun report_safety () Bool (=> (and c0100c166_rewards_accrual_enabled
         c0100c166_accrued_fees_present
         c0100c166_no_token_transfers_in
         c0100c166_caller_has_no_special_permissions)
    (or (not c0100c166_fees_counted_as_user_supplied)
        (not c0100c166_locked_assets_drained))))
(define-fun report_effects () Bool (and c0100c166_rewards_accrual_enabled
     c0100c166_accrued_fees_present
     c0100c166_no_token_transfers_in
     c0100c166_caller_has_no_special_permissions
     (not (or (not c0100c166_fees_counted_as_user_supplied)
              (not c0100c166_locked_assets_drained)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
