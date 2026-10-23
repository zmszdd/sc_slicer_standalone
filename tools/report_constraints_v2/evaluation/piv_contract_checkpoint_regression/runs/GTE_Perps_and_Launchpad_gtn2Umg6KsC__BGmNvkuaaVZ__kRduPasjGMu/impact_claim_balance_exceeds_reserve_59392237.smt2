; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c80542f44_balance0_after_update () Int)
(declare-fun c80542f44_balance1_after_update () Int)
(declare-fun c80542f44_reserve0_after_update () Int)
(declare-fun c80542f44_reserve1_after_update () Int)
(declare-fun c80542f44_time_elapsed () Int)
(declare-fun c80542f44_total_launchpad_fees () Int)
(assert
 (= c80542f44_balance0_after_update c80542f44_balance0_after_update))
(assert
 (= c80542f44_balance1_after_update c80542f44_balance1_after_update))
(assert
 (= c80542f44_reserve0_after_update c80542f44_reserve0_after_update))
(assert
 (= c80542f44_reserve1_after_update c80542f44_reserve1_after_update))
(assert
 (= c80542f44_time_elapsed c80542f44_time_elapsed))
(assert
 (= c80542f44_total_launchpad_fees c80542f44_total_launchpad_fees))
(define-fun report_preconditions () Bool (and (< 0 c80542f44_total_launchpad_fees) (= 0 c80542f44_time_elapsed)))
(define-fun report_safety () Bool (=> (and (= 0 c80542f44_time_elapsed) (< 0 c80542f44_total_launchpad_fees))
    (and (<= c80542f44_balance0_after_update c80542f44_reserve0_after_update)
         (<= c80542f44_balance1_after_update c80542f44_reserve1_after_update))))
(define-fun report_effects () Bool (and (= 0 c80542f44_time_elapsed)
     (< 0 c80542f44_total_launchpad_fees)
     (not (and (<= c80542f44_balance0_after_update
                   c80542f44_reserve0_after_update)
               (<= c80542f44_balance1_after_update
                   c80542f44_reserve1_after_update)))))
