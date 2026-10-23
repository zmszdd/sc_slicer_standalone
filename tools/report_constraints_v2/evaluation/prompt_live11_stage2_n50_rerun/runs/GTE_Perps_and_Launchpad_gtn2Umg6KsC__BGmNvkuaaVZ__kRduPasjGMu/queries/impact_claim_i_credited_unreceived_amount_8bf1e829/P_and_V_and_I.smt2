; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5f56815a_amount_actually_sent () Int)
(declare-fun c5f56815a_amount_in_credited () Int)
(declare-fun c5f56815a_time_elapsed () Int)
(declare-fun c5f56815a_total_launchpad_fees () Int)
(assert
 (= c5f56815a_amount_actually_sent c5f56815a_amount_actually_sent))
(assert
 (= c5f56815a_amount_in_credited c5f56815a_amount_in_credited))
(assert
 (= c5f56815a_time_elapsed c5f56815a_time_elapsed))
(assert
 (= c5f56815a_total_launchpad_fees c5f56815a_total_launchpad_fees))
(define-fun report_preconditions () Bool (and (< 0 c5f56815a_total_launchpad_fees) (= 0 c5f56815a_time_elapsed)))
(define-fun report_safety () Bool (=> (and (< 0 c5f56815a_total_launchpad_fees) (= 0 c5f56815a_time_elapsed))
    (= c5f56815a_amount_in_credited c5f56815a_amount_actually_sent)))
(define-fun report_effects () Bool (and (< 0 c5f56815a_total_launchpad_fees)
     (= 0 c5f56815a_time_elapsed)
     (not (= c5f56815a_amount_in_credited c5f56815a_amount_actually_sent))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
