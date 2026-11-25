; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5d461472_decimals_offset () Int)
(declare-fun c5d461472_erc4626_expected_share_decimals () Int)
(declare-fun c5d461472_integrator_quoted_value_incorrect () Bool)
(declare-fun c5d461472_reported_share_decimals () Int)
(declare-fun c5d461472_usdm_decimals () Int)
(assert
 (= c5d461472_decimals_offset c5d461472_decimals_offset))
(assert
 (= c5d461472_erc4626_expected_share_decimals c5d461472_erc4626_expected_share_decimals))
(assert
 (= c5d461472_integrator_quoted_value_incorrect c5d461472_integrator_quoted_value_incorrect))
(assert
 (= c5d461472_reported_share_decimals c5d461472_reported_share_decimals))
(assert
 (= c5d461472_usdm_decimals c5d461472_usdm_decimals))
(define-fun report_preconditions () Bool (and (= 6 c5d461472_usdm_decimals)
     (= 6 c5d461472_decimals_offset)
     (= 6 c5d461472_reported_share_decimals)
     c5d461472_integrator_quoted_value_incorrect))
(define-fun report_safety () Bool (=> (= c5d461472_erc4626_expected_share_decimals
       (+ c5d461472_usdm_decimals c5d461472_decimals_offset))
    (= c5d461472_reported_share_decimals
       c5d461472_erc4626_expected_share_decimals)))
(define-fun report_effects () Bool (and (= c5d461472_erc4626_expected_share_decimals
        (+ c5d461472_usdm_decimals c5d461472_decimals_offset))
     c5d461472_integrator_quoted_value_incorrect
     (not (= c5d461472_reported_share_decimals
             c5d461472_erc4626_expected_share_decimals))
     c5d461472_integrator_quoted_value_incorrect
     c5d461472_integrator_quoted_value_incorrect))
(assert report_preconditions)
(check-sat)
(get-model)
