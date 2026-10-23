; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c80542f44_balance0 () Int)
(declare-fun c80542f44_balance1 () Int)
(declare-fun c80542f44_launchpad_fees_nonzero () Bool)
(declare-fun c80542f44_reserve0 () Int)
(declare-fun c80542f44_reserve1 () Int)
(declare-fun c80542f44_time_elapsed () Int)
(assert
 (= c80542f44_balance0 c80542f44_balance0))
(assert
 (= c80542f44_balance1 c80542f44_balance1))
(assert
 (= c80542f44_launchpad_fees_nonzero c80542f44_launchpad_fees_nonzero))
(assert
 (= c80542f44_reserve0 c80542f44_reserve0))
(assert
 (= c80542f44_reserve1 c80542f44_reserve1))
(assert
 (= c80542f44_time_elapsed c80542f44_time_elapsed))
(define-fun report_preconditions () Bool (and c80542f44_launchpad_fees_nonzero (= 0 c80542f44_time_elapsed)))
(define-fun report_safety () Bool (=> (and c80542f44_launchpad_fees_nonzero (= 0 c80542f44_time_elapsed))
    (and (<= c80542f44_balance0 c80542f44_reserve0)
         (<= c80542f44_balance1 c80542f44_reserve1))))
(define-fun report_effects () Bool (and c80542f44_launchpad_fees_nonzero
     (= 0 c80542f44_time_elapsed)
     (not (and (<= c80542f44_balance0 c80542f44_reserve0)
               (<= c80542f44_balance1 c80542f44_reserve1)))))
(assert report_preconditions)
(check-sat)
(get-model)
