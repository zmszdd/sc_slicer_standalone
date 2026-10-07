; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun total_supply () Int)
(declare-fun total_assets () Int)
(declare-fun assets_to_fulfill () Int)
(declare-fun shares_received () Int)
(declare-fun tiny_total_assets () Bool)
(assert
 (= total_supply total_supply))
(assert
 (= total_assets total_assets))
(assert
 (= assets_to_fulfill assets_to_fulfill))
(assert
 (= shares_received shares_received))
(assert
 (= tiny_total_assets tiny_total_assets))
(define-fun report_preconditions () Bool (and (= 1000000 total_supply) tiny_total_assets tiny_total_assets))
(define-fun report_safety () Bool (=> (and (= 1000000 total_supply) tiny_total_assets)
    (<= (* shares_received total_assets) (* assets_to_fulfill total_supply))))
(define-fun report_effects () Bool (and (= 1000000 total_supply)
     tiny_total_assets
     (not (<= (* shares_received total_assets)
              (* assets_to_fulfill total_supply)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
