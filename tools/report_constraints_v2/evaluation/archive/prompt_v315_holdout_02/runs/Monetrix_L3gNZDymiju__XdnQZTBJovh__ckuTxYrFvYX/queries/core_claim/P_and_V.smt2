; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun usdm_decimals () Int)
(declare-fun decimals_offset () Int)
(declare-fun reported_decimals () Int)
(declare-fun expected_decimals () Int)
(assert
 (= usdm_decimals usdm_decimals))
(assert
 (= decimals_offset decimals_offset))
(assert
 (= reported_decimals reported_decimals))
(assert
 (= expected_decimals expected_decimals))
(define-fun report_preconditions () Bool (and (= 6 usdm_decimals) (= 6 decimals_offset) (= 6 reported_decimals)))
(define-fun report_safety () Bool (=> (and (= 6 usdm_decimals) (= 6 decimals_offset))
    (= reported_decimals expected_decimals)))
(define-fun report_effects () Bool (and (= 6 usdm_decimals)
     (= 6 decimals_offset)
     (not (= reported_decimals expected_decimals))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
