; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun msg_value_exceeds_fee () Bool)
(declare-fun messenger_fee_check_passed () Bool)
(declare-fun caller_used_buffer_helper () Bool)
(declare-fun unstake_call_completed () Bool)
(assert
 (= msg_value_exceeds_fee msg_value_exceeds_fee))
(assert
 (= messenger_fee_check_passed messenger_fee_check_passed))
(assert
 (= caller_used_buffer_helper caller_used_buffer_helper))
(assert
 (= unstake_call_completed unstake_call_completed))
(define-fun report_preconditions () Bool (and caller_used_buffer_helper msg_value_exceeds_fee messenger_fee_check_passed))
(define-fun report_safety () Bool (=> (and caller_used_buffer_helper
         msg_value_exceeds_fee
         messenger_fee_check_passed)
    unstake_call_completed))
(define-fun report_effects () Bool (and caller_used_buffer_helper
     msg_value_exceeds_fee
     messenger_fee_check_passed
     (not unstake_call_completed)))
(assert report_preconditions)
(check-sat)
(get-model)
