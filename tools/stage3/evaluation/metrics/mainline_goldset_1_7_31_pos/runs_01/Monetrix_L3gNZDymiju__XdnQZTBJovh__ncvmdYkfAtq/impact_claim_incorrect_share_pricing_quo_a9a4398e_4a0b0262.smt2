; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3d760501_decimals_offset () Int)
(declare-fun c3d760501_expected_susdm_decimals () Int)
(declare-fun c3d760501_integrator_quoted_value_incorrect () Bool)
(declare-fun c3d760501_susdm_decimals () Int)
(declare-fun c3d760501_usdm_decimals () Int)
(assert
 (= c3d760501_decimals_offset c3d760501_decimals_offset))
(assert
 (= c3d760501_expected_susdm_decimals c3d760501_expected_susdm_decimals))
(assert
 (= c3d760501_integrator_quoted_value_incorrect c3d760501_integrator_quoted_value_incorrect))
(assert
 (= c3d760501_susdm_decimals c3d760501_susdm_decimals))
(assert
 (= c3d760501_usdm_decimals c3d760501_usdm_decimals))
(define-fun report_preconditions () Bool (and (= 6 c3d760501_usdm_decimals)
     (= 6 c3d760501_decimals_offset)
     (= 6 c3d760501_susdm_decimals)
     c3d760501_integrator_quoted_value_incorrect))
(define-fun report_safety () Bool (=> (= c3d760501_expected_susdm_decimals
       (+ c3d760501_usdm_decimals c3d760501_decimals_offset))
    (= c3d760501_susdm_decimals c3d760501_expected_susdm_decimals)))
(define-fun report_effects () Bool (and (= c3d760501_expected_susdm_decimals
        (+ c3d760501_usdm_decimals c3d760501_decimals_offset))
     c3d760501_integrator_quoted_value_incorrect
     (not (= c3d760501_susdm_decimals c3d760501_expected_susdm_decimals))
     c3d760501_integrator_quoted_value_incorrect))
