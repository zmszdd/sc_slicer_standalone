; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfc0377bb_guard_passed () Bool)
(declare-fun cfc0377bb_spot_price_manipulated () Bool)
(assert
 (= cfc0377bb_guard_passed cfc0377bb_guard_passed))
(assert
 (= cfc0377bb_spot_price_manipulated cfc0377bb_spot_price_manipulated))
(define-fun report_preconditions () Bool cfc0377bb_spot_price_manipulated)
(define-fun report_safety () Bool (=> cfc0377bb_spot_price_manipulated (not cfc0377bb_guard_passed)))
(define-fun report_effects () Bool (and cfc0377bb_spot_price_manipulated (not (not cfc0377bb_guard_passed))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
