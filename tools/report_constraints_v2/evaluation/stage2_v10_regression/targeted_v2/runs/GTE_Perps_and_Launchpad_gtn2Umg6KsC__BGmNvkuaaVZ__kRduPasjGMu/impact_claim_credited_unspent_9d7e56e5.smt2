; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c20b6e798_amount_actually_sent () Int)
(declare-fun c20b6e798_amount_in_credited () Int)
(declare-fun c20b6e798_time_elapsed () Int)
(declare-fun c20b6e798_total_launchpad_fees_nonzero () Bool)
(assert
 (= c20b6e798_amount_actually_sent c20b6e798_amount_actually_sent))
(assert
 (= c20b6e798_amount_in_credited c20b6e798_amount_in_credited))
(assert
 (= c20b6e798_time_elapsed c20b6e798_time_elapsed))
(assert
 (= c20b6e798_total_launchpad_fees_nonzero c20b6e798_total_launchpad_fees_nonzero))
(define-fun report_preconditions () Bool (and c20b6e798_total_launchpad_fees_nonzero (= 0 c20b6e798_time_elapsed)))
(define-fun report_safety () Bool (=> (and c20b6e798_total_launchpad_fees_nonzero (= 0 c20b6e798_time_elapsed))
    (= c20b6e798_amount_in_credited c20b6e798_amount_actually_sent)))
(define-fun report_effects () Bool (and c20b6e798_total_launchpad_fees_nonzero
     (= 0 c20b6e798_time_elapsed)
     (not (= c20b6e798_amount_in_credited c20b6e798_amount_actually_sent))))
