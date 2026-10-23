; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce60a4138_deposit_fee_tokens () Int)
(declare-fun ce60a4138_dispute_amount_sent_tokens () Int)
(declare-fun ce60a4138_fot_token_is_dispute_token () Bool)
(declare-fun ce60a4138_no_recovery_path_available () Bool)
(declare-fun ce60a4138_resolve_completed () Bool)
(declare-fun ce60a4138_resolve_reverted () Bool)
(assert
 (= ce60a4138_deposit_fee_tokens ce60a4138_deposit_fee_tokens))
(assert
 (= ce60a4138_dispute_amount_sent_tokens ce60a4138_dispute_amount_sent_tokens))
(assert
 (= ce60a4138_fot_token_is_dispute_token ce60a4138_fot_token_is_dispute_token))
(assert
 (= ce60a4138_no_recovery_path_available ce60a4138_no_recovery_path_available))
(assert
 (= ce60a4138_resolve_completed ce60a4138_resolve_completed))
(assert
 (= ce60a4138_resolve_reverted ce60a4138_resolve_reverted))
(define-fun report_preconditions () Bool (and ce60a4138_fot_token_is_dispute_token
     (= 1000 ce60a4138_dispute_amount_sent_tokens)
     (= 10 ce60a4138_deposit_fee_tokens)
     ce60a4138_no_recovery_path_available))
(define-fun report_safety () Bool (=> (and ce60a4138_fot_token_is_dispute_token
         (= 1000 ce60a4138_dispute_amount_sent_tokens)
         (= 10 ce60a4138_deposit_fee_tokens)
         ce60a4138_no_recovery_path_available)
    (and ce60a4138_resolve_completed (not ce60a4138_resolve_reverted))))
(define-fun report_effects () Bool (and ce60a4138_fot_token_is_dispute_token
     (= 1000 ce60a4138_dispute_amount_sent_tokens)
     (= 10 ce60a4138_deposit_fee_tokens)
     ce60a4138_no_recovery_path_available
     (not (and ce60a4138_resolve_completed (not ce60a4138_resolve_reverted)))))
