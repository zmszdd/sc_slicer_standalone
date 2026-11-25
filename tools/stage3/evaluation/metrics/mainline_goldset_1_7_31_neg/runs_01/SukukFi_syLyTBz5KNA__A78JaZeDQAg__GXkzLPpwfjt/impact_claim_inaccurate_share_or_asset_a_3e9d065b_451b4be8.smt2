; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7d2a206a_inaccurate_share_or_asset_amounts_observed () Bool)
(declare-fun c7d2a206a_investment_assets_calc_includes_rbalance () Bool)
(declare-fun c7d2a206a_rbalance_reversible_via_cancel () Bool)
(declare-fun c7d2a206a_total_investment_assets_includes_rbalance () Bool)
(assert
 (= c7d2a206a_inaccurate_share_or_asset_amounts_observed c7d2a206a_inaccurate_share_or_asset_amounts_observed))
(assert
 (= c7d2a206a_investment_assets_calc_includes_rbalance c7d2a206a_investment_assets_calc_includes_rbalance))
(assert
 (= c7d2a206a_rbalance_reversible_via_cancel c7d2a206a_rbalance_reversible_via_cancel))
(assert
 (= c7d2a206a_total_investment_assets_includes_rbalance c7d2a206a_total_investment_assets_includes_rbalance))
(define-fun report_preconditions () Bool (and c7d2a206a_total_investment_assets_includes_rbalance
     c7d2a206a_rbalance_reversible_via_cancel))
(define-fun report_safety () Bool (=> c7d2a206a_total_investment_assets_includes_rbalance
    (not c7d2a206a_investment_assets_calc_includes_rbalance)))
(define-fun report_effects () Bool (and c7d2a206a_total_investment_assets_includes_rbalance
     c7d2a206a_investment_assets_calc_includes_rbalance
     c7d2a206a_inaccurate_share_or_asset_amounts_observed))
