; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun underlying_decimals () Int)
(declare-fun decimals_offset () Int)
(declare-fun reported_decimals () Int)
(declare-fun expected_decimals () Int)
(assert
 (= underlying_decimals underlying_decimals))
(assert
 (= decimals_offset decimals_offset))
(assert
 (= reported_decimals reported_decimals))
(assert
 (= expected_decimals expected_decimals))
(define-fun report_preconditions () Bool (and (= 6 underlying_decimals) (= 6 decimals_offset) (= 6 reported_decimals)))
(define-fun report_safety () Bool (=> (= expected_decimals (+ underlying_decimals decimals_offset))
    (=> (and (= 6 underlying_decimals)
             (= 6 decimals_offset)
             (= 6 reported_decimals))
        (= reported_decimals expected_decimals))))
(define-fun report_effects () Bool (and (= expected_decimals (+ underlying_decimals decimals_offset))
     (= 6 underlying_decimals)
     (= 6 decimals_offset)
     (= 6 reported_decimals)
     (not (= reported_decimals expected_decimals))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
