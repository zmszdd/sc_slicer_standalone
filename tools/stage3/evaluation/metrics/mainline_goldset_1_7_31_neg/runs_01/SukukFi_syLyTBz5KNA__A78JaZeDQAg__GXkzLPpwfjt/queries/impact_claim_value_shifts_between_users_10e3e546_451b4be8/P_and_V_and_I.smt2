; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf3f0891b_conversion_executed_on_rbalance_inclusive_value () Bool)
(declare-fun cf3f0891b_investment_assets_include_rbalance () Bool)
(declare-fun cf3f0891b_rbalance_later_corrected () Bool)
(declare-fun cf3f0891b_rbalance_reversible_via_cancel () Bool)
(declare-fun cf3f0891b_total_investment_assets_includes_rbalance () Bool)
(declare-fun cf3f0891b_value_shifts_between_users_observed () Bool)
(assert
 (= cf3f0891b_conversion_executed_on_rbalance_inclusive_value cf3f0891b_conversion_executed_on_rbalance_inclusive_value))
(assert
 (= cf3f0891b_investment_assets_include_rbalance cf3f0891b_investment_assets_include_rbalance))
(assert
 (= cf3f0891b_rbalance_later_corrected cf3f0891b_rbalance_later_corrected))
(assert
 (= cf3f0891b_rbalance_reversible_via_cancel cf3f0891b_rbalance_reversible_via_cancel))
(assert
 (= cf3f0891b_total_investment_assets_includes_rbalance cf3f0891b_total_investment_assets_includes_rbalance))
(assert
 (= cf3f0891b_value_shifts_between_users_observed cf3f0891b_value_shifts_between_users_observed))
(define-fun report_preconditions () Bool (and cf3f0891b_total_investment_assets_includes_rbalance
     cf3f0891b_rbalance_reversible_via_cancel))
(define-fun report_safety () Bool (=> cf3f0891b_total_investment_assets_includes_rbalance
    (not cf3f0891b_investment_assets_include_rbalance)))
(define-fun report_effects () Bool (and cf3f0891b_total_investment_assets_includes_rbalance
     cf3f0891b_investment_assets_include_rbalance
     cf3f0891b_conversion_executed_on_rbalance_inclusive_value
     cf3f0891b_rbalance_later_corrected
     cf3f0891b_value_shifts_between_users_observed))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
