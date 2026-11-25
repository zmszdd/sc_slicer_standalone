; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfc3b45b3_actual_received_amount () Int)
(declare-fun cfc3b45b3_credited_balance_amount () Int)
(declare-fun cfc3b45b3_fot_token_is_whitelisted_reward_token () Bool)
(declare-fun cfc3b45b3_fund_loss_occurred () Bool)
(declare-fun cfc3b45b3_transfer_received_amount () Int)
(declare-fun cfc3b45b3_transfer_requested_amount () Int)
(assert
 (= cfc3b45b3_actual_received_amount cfc3b45b3_actual_received_amount))
(assert
 (= cfc3b45b3_credited_balance_amount cfc3b45b3_credited_balance_amount))
(assert
 (= cfc3b45b3_fot_token_is_whitelisted_reward_token cfc3b45b3_fot_token_is_whitelisted_reward_token))
(assert
 (= cfc3b45b3_fund_loss_occurred cfc3b45b3_fund_loss_occurred))
(assert
 (= cfc3b45b3_transfer_received_amount cfc3b45b3_transfer_received_amount))
(assert
 (= cfc3b45b3_transfer_requested_amount cfc3b45b3_transfer_requested_amount))
(define-fun report_preconditions () Bool (and cfc3b45b3_fot_token_is_whitelisted_reward_token
     (< cfc3b45b3_transfer_received_amount cfc3b45b3_transfer_requested_amount)))
(define-fun report_safety () Bool (=> cfc3b45b3_fot_token_is_whitelisted_reward_token
    (= cfc3b45b3_credited_balance_amount cfc3b45b3_actual_received_amount)))
(define-fun report_effects () Bool (and cfc3b45b3_fot_token_is_whitelisted_reward_token
     (not (= cfc3b45b3_credited_balance_amount cfc3b45b3_actual_received_amount))
     cfc3b45b3_fund_loss_occurred))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
