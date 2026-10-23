; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2eaecf0b_later_depositors_bought_worthless_shares () Bool)
(declare-fun c2eaecf0b_total_assets_before_first_fulfillment () Int)
(declare-fun c2eaecf0b_total_supply_at_bootstrap () Int)
(declare-fun c2eaecf0b_vault_assets_at_bootstrap () Int)
(declare-fun c2eaecf0b_zero_supply () Int)
(assert
 (= c2eaecf0b_later_depositors_bought_worthless_shares c2eaecf0b_later_depositors_bought_worthless_shares))
(assert
 (= c2eaecf0b_total_assets_before_first_fulfillment c2eaecf0b_total_assets_before_first_fulfillment))
(assert
 (= c2eaecf0b_total_supply_at_bootstrap c2eaecf0b_total_supply_at_bootstrap))
(assert
 (= c2eaecf0b_vault_assets_at_bootstrap c2eaecf0b_vault_assets_at_bootstrap))
(assert
 (= c2eaecf0b_zero_supply c2eaecf0b_zero_supply))
(define-fun report_preconditions () Bool (and (= 1000000 c2eaecf0b_total_supply_at_bootstrap)
     (= 0 c2eaecf0b_vault_assets_at_bootstrap)
     (= 1 c2eaecf0b_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 1 c2eaecf0b_total_assets_before_first_fulfillment)
    (= c2eaecf0b_total_supply_at_bootstrap c2eaecf0b_zero_supply)))
(define-fun report_effects () Bool c2eaecf0b_later_depositors_bought_worthless_shares)
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
