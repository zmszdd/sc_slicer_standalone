; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce60a4138_deposit_fee_deducted () Bool)
(declare-fun ce60a4138_dispute_deposit_occurred () Bool)
(declare-fun ce60a4138_fot_token_is_dispute_token () Bool)
(declare-fun ce60a4138_resolve_completed () Bool)
(assert
 (= ce60a4138_deposit_fee_deducted ce60a4138_deposit_fee_deducted))
(assert
 (= ce60a4138_dispute_deposit_occurred ce60a4138_dispute_deposit_occurred))
(assert
 (= ce60a4138_fot_token_is_dispute_token ce60a4138_fot_token_is_dispute_token))
(assert
 (= ce60a4138_resolve_completed ce60a4138_resolve_completed))
(define-fun report_preconditions () Bool (and ce60a4138_fot_token_is_dispute_token
     ce60a4138_dispute_deposit_occurred
     ce60a4138_deposit_fee_deducted))
(define-fun report_safety () Bool (=> (and ce60a4138_fot_token_is_dispute_token
         ce60a4138_dispute_deposit_occurred
         ce60a4138_deposit_fee_deducted)
    ce60a4138_resolve_completed))
(define-fun report_effects () Bool (and ce60a4138_fot_token_is_dispute_token
     ce60a4138_dispute_deposit_occurred
     ce60a4138_deposit_fee_deducted
     (not ce60a4138_resolve_completed)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
