; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8af912f2_decimals_offset () Int)
(declare-fun c8af912f2_deposit_mint_failed () Bool)
(declare-fun c8af912f2_erc4626_expected_share_decimals () Int)
(declare-fun c8af912f2_reported_share_decimals () Int)
(declare-fun c8af912f2_usdm_decimals () Int)
(assert
 (= c8af912f2_decimals_offset c8af912f2_decimals_offset))
(assert
 (= c8af912f2_deposit_mint_failed c8af912f2_deposit_mint_failed))
(assert
 (= c8af912f2_erc4626_expected_share_decimals c8af912f2_erc4626_expected_share_decimals))
(assert
 (= c8af912f2_reported_share_decimals c8af912f2_reported_share_decimals))
(assert
 (= c8af912f2_usdm_decimals c8af912f2_usdm_decimals))
(define-fun report_preconditions () Bool (and (= 6 c8af912f2_usdm_decimals)
     (= 6 c8af912f2_decimals_offset)
     (= 6 c8af912f2_reported_share_decimals)))
(define-fun report_safety () Bool (=> (= c8af912f2_erc4626_expected_share_decimals
       (+ c8af912f2_usdm_decimals c8af912f2_decimals_offset))
    (=> (= 6 c8af912f2_reported_share_decimals)
        (= c8af912f2_reported_share_decimals
           c8af912f2_erc4626_expected_share_decimals))))
(define-fun report_effects () Bool (and (= c8af912f2_erc4626_expected_share_decimals
        (+ c8af912f2_usdm_decimals c8af912f2_decimals_offset))
     (= 6 c8af912f2_reported_share_decimals)
     (not (= c8af912f2_reported_share_decimals
             c8af912f2_erc4626_expected_share_decimals))
     c8af912f2_deposit_mint_failed))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
