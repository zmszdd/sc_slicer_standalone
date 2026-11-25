; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c94122ff5_decimals_offset () Int)
(declare-fun c94122ff5_erc4626_expected_share_decimals () Int)
(declare-fun c94122ff5_integrator_scales_by_reported_decimals () Bool)
(declare-fun c94122ff5_reported_share_decimals () Int)
(declare-fun c94122ff5_slippage_protection_wrong () Bool)
(declare-fun c94122ff5_usdm_decimals () Int)
(assert
 (= c94122ff5_decimals_offset c94122ff5_decimals_offset))
(assert
 (= c94122ff5_erc4626_expected_share_decimals c94122ff5_erc4626_expected_share_decimals))
(assert
 (= c94122ff5_integrator_scales_by_reported_decimals c94122ff5_integrator_scales_by_reported_decimals))
(assert
 (= c94122ff5_reported_share_decimals c94122ff5_reported_share_decimals))
(assert
 (= c94122ff5_slippage_protection_wrong c94122ff5_slippage_protection_wrong))
(assert
 (= c94122ff5_usdm_decimals c94122ff5_usdm_decimals))
(define-fun report_preconditions () Bool (and (= 6 c94122ff5_usdm_decimals)
     (= 6 c94122ff5_decimals_offset)
     (= 6 c94122ff5_reported_share_decimals)
     c94122ff5_integrator_scales_by_reported_decimals))
(define-fun report_safety () Bool (=> (= c94122ff5_erc4626_expected_share_decimals
       (+ c94122ff5_usdm_decimals c94122ff5_decimals_offset))
    (= c94122ff5_reported_share_decimals
       c94122ff5_erc4626_expected_share_decimals)))
(define-fun report_effects () Bool (and (= c94122ff5_erc4626_expected_share_decimals
        (+ c94122ff5_usdm_decimals c94122ff5_decimals_offset))
     c94122ff5_integrator_scales_by_reported_decimals
     (not (= c94122ff5_reported_share_decimals
             c94122ff5_erc4626_expected_share_decimals))
     c94122ff5_slippage_protection_wrong
     c94122ff5_integrator_scales_by_reported_decimals))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
