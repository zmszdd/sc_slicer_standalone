; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c72c5b129_asset_decimals () Int)
(declare-fun c72c5b129_decimals_offset () Int)
(declare-fun c72c5b129_expected_decimals () Int)
(declare-fun c72c5b129_reported_decimals () Int)
(declare-fun c72c5b129_shares_misreported () Bool)
(assert
 (= c72c5b129_asset_decimals c72c5b129_asset_decimals))
(assert
 (= c72c5b129_decimals_offset c72c5b129_decimals_offset))
(assert
 (= c72c5b129_expected_decimals c72c5b129_expected_decimals))
(assert
 (= c72c5b129_reported_decimals c72c5b129_reported_decimals))
(assert
 (= c72c5b129_shares_misreported c72c5b129_shares_misreported))
(define-fun report_preconditions () Bool (and (= 6 c72c5b129_asset_decimals)
     (= 6 c72c5b129_decimals_offset)
     (= 6 c72c5b129_reported_decimals)
     c72c5b129_shares_misreported))
(define-fun report_safety () Bool (=> (= c72c5b129_expected_decimals
       (+ c72c5b129_asset_decimals c72c5b129_decimals_offset))
    (= c72c5b129_reported_decimals c72c5b129_expected_decimals)))
(define-fun report_effects () Bool (and (= c72c5b129_expected_decimals
        (+ c72c5b129_asset_decimals c72c5b129_decimals_offset))
     c72c5b129_shares_misreported
     (not (= c72c5b129_reported_decimals c72c5b129_expected_decimals))
     c72c5b129_shares_misreported))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
