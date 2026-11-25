; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c289ad2e7_decimals_offset () Int)
(declare-fun c289ad2e7_erc4626_expected_share_decimals () Int)
(declare-fun c289ad2e7_reported_share_decimals () Int)
(declare-fun c289ad2e7_ui_amount_misleading () Bool)
(declare-fun c289ad2e7_usdm_decimals () Int)
(assert
 (= c289ad2e7_decimals_offset c289ad2e7_decimals_offset))
(assert
 (= c289ad2e7_erc4626_expected_share_decimals c289ad2e7_erc4626_expected_share_decimals))
(assert
 (= c289ad2e7_reported_share_decimals c289ad2e7_reported_share_decimals))
(assert
 (= c289ad2e7_ui_amount_misleading c289ad2e7_ui_amount_misleading))
(assert
 (= c289ad2e7_usdm_decimals c289ad2e7_usdm_decimals))
(define-fun report_preconditions () Bool (and (= 6 c289ad2e7_usdm_decimals)
     (= 6 c289ad2e7_decimals_offset)
     (= 6 c289ad2e7_reported_share_decimals)
     c289ad2e7_ui_amount_misleading))
(define-fun report_safety () Bool (=> (= c289ad2e7_erc4626_expected_share_decimals
       (+ c289ad2e7_usdm_decimals c289ad2e7_decimals_offset))
    (= c289ad2e7_reported_share_decimals
       c289ad2e7_erc4626_expected_share_decimals)))
(define-fun report_effects () Bool (and (= c289ad2e7_erc4626_expected_share_decimals
        (+ c289ad2e7_usdm_decimals c289ad2e7_decimals_offset))
     c289ad2e7_ui_amount_misleading
     (not (= c289ad2e7_reported_share_decimals
             c289ad2e7_erc4626_expected_share_decimals))
     c289ad2e7_ui_amount_misleading))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
