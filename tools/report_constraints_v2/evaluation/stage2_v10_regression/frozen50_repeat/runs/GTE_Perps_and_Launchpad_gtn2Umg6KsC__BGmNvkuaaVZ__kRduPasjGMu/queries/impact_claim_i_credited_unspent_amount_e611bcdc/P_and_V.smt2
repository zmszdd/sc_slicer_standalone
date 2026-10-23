; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce0757171_credited_amount () Int)
(declare-fun ce0757171_launchpad_fees_accrued () Bool)
(declare-fun ce0757171_sent_amount () Int)
(declare-fun ce0757171_time_elapsed () Int)
(assert
 (= ce0757171_credited_amount ce0757171_credited_amount))
(assert
 (= ce0757171_launchpad_fees_accrued ce0757171_launchpad_fees_accrued))
(assert
 (= ce0757171_sent_amount ce0757171_sent_amount))
(assert
 (= ce0757171_time_elapsed ce0757171_time_elapsed))
(define-fun report_preconditions () Bool (and ce0757171_launchpad_fees_accrued (= 0 ce0757171_time_elapsed)))
(define-fun report_safety () Bool (=> (and ce0757171_launchpad_fees_accrued (= 0 ce0757171_time_elapsed))
    (<= ce0757171_credited_amount ce0757171_sent_amount)))
(define-fun report_effects () Bool (and ce0757171_launchpad_fees_accrued
     (= 0 ce0757171_time_elapsed)
     (not (<= ce0757171_credited_amount ce0757171_sent_amount))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
