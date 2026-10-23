; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c28a31543_share_price_consistent_with_assets () Bool)
(declare-fun c28a31543_share_price_reflects_assets () Bool)
(assert
 (= c28a31543_share_price_consistent_with_assets c28a31543_share_price_consistent_with_assets))
(assert
 (= c28a31543_share_price_reflects_assets c28a31543_share_price_reflects_assets))
(define-fun report_preconditions () Bool c28a31543_share_price_reflects_assets)
(define-fun report_safety () Bool (=> (not c28a31543_share_price_consistent_with_assets)
    (=> c28a31543_share_price_reflects_assets
        (= c28a31543_share_price_consistent_with_assets
           c28a31543_share_price_reflects_assets))))
(define-fun report_effects () Bool (and (not c28a31543_share_price_consistent_with_assets)
     c28a31543_share_price_reflects_assets
     (not (= c28a31543_share_price_consistent_with_assets
             c28a31543_share_price_reflects_assets))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
