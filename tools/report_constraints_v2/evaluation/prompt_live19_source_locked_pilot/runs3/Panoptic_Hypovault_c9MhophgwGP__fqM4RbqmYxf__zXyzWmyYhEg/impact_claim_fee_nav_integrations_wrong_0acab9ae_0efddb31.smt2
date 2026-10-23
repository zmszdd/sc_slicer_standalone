; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7a039d1d_share_price_integrations_correct () Bool)
(declare-fun c7a039d1d_total_assets_before_first_fulfillment () Int)
(declare-fun c7a039d1d_total_supply_at_bootstrap () Int)
(declare-fun c7a039d1d_underlying_assets_at_bootstrap () Int)
(assert
 (= c7a039d1d_share_price_integrations_correct c7a039d1d_share_price_integrations_correct))
(assert
 (= c7a039d1d_total_assets_before_first_fulfillment c7a039d1d_total_assets_before_first_fulfillment))
(assert
 (= c7a039d1d_total_supply_at_bootstrap c7a039d1d_total_supply_at_bootstrap))
(assert
 (= c7a039d1d_underlying_assets_at_bootstrap c7a039d1d_underlying_assets_at_bootstrap))
(define-fun report_preconditions () Bool (and (= 1000000 c7a039d1d_total_supply_at_bootstrap)
     (= 0 c7a039d1d_underlying_assets_at_bootstrap)
     (= 1 c7a039d1d_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 0 c7a039d1d_total_supply_at_bootstrap)
    (= 0 c7a039d1d_underlying_assets_at_bootstrap)))
(define-fun report_effects () Bool (not c7a039d1d_share_price_integrations_correct))
