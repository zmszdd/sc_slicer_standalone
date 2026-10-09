; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cumulative_price_snapshot_read () Bool)
(declare-fun max_slippage_supplied () Bool)
(declare-fun guard_passed () Bool)
(declare-fun deviation_exceeds_tolerance () Bool)
(assert
 (= cumulative_price_snapshot_read cumulative_price_snapshot_read))
(assert
 (= max_slippage_supplied max_slippage_supplied))
(assert
 (= guard_passed guard_passed))
(assert
 (= deviation_exceeds_tolerance deviation_exceeds_tolerance))
(define-fun report_preconditions () Bool (and cumulative_price_snapshot_read max_slippage_supplied))
(define-fun report_safety () Bool (=> deviation_exceeds_tolerance
    (=> guard_passed (not deviation_exceeds_tolerance))))
(define-fun report_effects () Bool (and deviation_exceeds_tolerance
     guard_passed
     (not (not deviation_exceeds_tolerance))))
(assert report_preconditions)
(check-sat)
(get-model)
