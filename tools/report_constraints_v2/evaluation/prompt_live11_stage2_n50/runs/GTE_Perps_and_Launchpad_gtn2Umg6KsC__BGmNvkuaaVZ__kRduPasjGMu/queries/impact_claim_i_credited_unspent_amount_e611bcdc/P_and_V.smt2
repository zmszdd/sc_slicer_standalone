; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce0757171_actually_sent_amount () Int)
(declare-fun ce0757171_credited_amount_in () Int)
(declare-fun ce0757171_time_elapsed () Int)
(declare-fun ce0757171_total_launchpad_fees () Int)
(assert
 (= ce0757171_actually_sent_amount ce0757171_actually_sent_amount))
(assert
 (= ce0757171_credited_amount_in ce0757171_credited_amount_in))
(assert
 (= ce0757171_time_elapsed ce0757171_time_elapsed))
(assert
 (= ce0757171_total_launchpad_fees ce0757171_total_launchpad_fees))
(define-fun report_preconditions () Bool (and (< 0 ce0757171_total_launchpad_fees) (= 0 ce0757171_time_elapsed)))
(define-fun report_safety () Bool (=> (and (< 0 ce0757171_total_launchpad_fees) (= 0 ce0757171_time_elapsed))
    (= ce0757171_credited_amount_in ce0757171_actually_sent_amount)))
(define-fun report_effects () Bool (and (< 0 ce0757171_total_launchpad_fees)
     (= 0 ce0757171_time_elapsed)
     (not (= ce0757171_credited_amount_in ce0757171_actually_sent_amount))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
