; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce60a4138_dispute_amount_sent () Int)
(declare-fun ce60a4138_fot_fee_deducted () Bool)
(declare-fun ce60a4138_fot_token_is_dispute_token () Bool)
(declare-fun ce60a4138_no_recovery_path_available () Bool)
(declare-fun ce60a4138_resolve_completes () Bool)
(assert
 (= ce60a4138_dispute_amount_sent ce60a4138_dispute_amount_sent))
(assert
 (= ce60a4138_fot_fee_deducted ce60a4138_fot_fee_deducted))
(assert
 (= ce60a4138_fot_token_is_dispute_token ce60a4138_fot_token_is_dispute_token))
(assert
 (= ce60a4138_no_recovery_path_available ce60a4138_no_recovery_path_available))
(assert
 (= ce60a4138_resolve_completes ce60a4138_resolve_completes))
(define-fun report_preconditions () Bool (and ce60a4138_fot_token_is_dispute_token
     (= 1000 ce60a4138_dispute_amount_sent)
     ce60a4138_fot_fee_deducted
     ce60a4138_no_recovery_path_available))
(define-fun report_safety () Bool (=> (and ce60a4138_fot_token_is_dispute_token
         (= 1000 ce60a4138_dispute_amount_sent)
         ce60a4138_fot_fee_deducted
         ce60a4138_no_recovery_path_available)
    ce60a4138_resolve_completes))
(define-fun report_effects () Bool (and ce60a4138_fot_token_is_dispute_token
     (= 1000 ce60a4138_dispute_amount_sent)
     ce60a4138_fot_fee_deducted
     ce60a4138_no_recovery_path_available
     (not ce60a4138_resolve_completes)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
