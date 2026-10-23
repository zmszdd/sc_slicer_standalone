; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c93954677_first_depositor_share_control () Bool)
(declare-fun c93954677_total_supply_at_construction () Int)
(declare-fun c93954677_vault_assets_before_first_deposit () Int)
(declare-fun c93954677_zero_assets () Int)
(declare-fun c93954677_zero_supply () Int)
(assert
 (= c93954677_first_depositor_share_control c93954677_first_depositor_share_control))
(assert
 (= c93954677_total_supply_at_construction c93954677_total_supply_at_construction))
(assert
 (= c93954677_vault_assets_before_first_deposit c93954677_vault_assets_before_first_deposit))
(assert
 (= c93954677_zero_assets c93954677_zero_assets))
(assert
 (= c93954677_zero_supply c93954677_zero_supply))
(define-fun report_preconditions () Bool (and (= 1000000 c93954677_total_supply_at_construction)
     (= c93954677_vault_assets_before_first_deposit c93954677_zero_assets)))
(define-fun report_safety () Bool (=> c93954677_first_depositor_share_control
    (=> (= c93954677_vault_assets_before_first_deposit c93954677_zero_assets)
        (= c93954677_total_supply_at_construction c93954677_zero_supply))))
(define-fun report_effects () Bool (and c93954677_first_depositor_share_control
     (= c93954677_vault_assets_before_first_deposit c93954677_zero_assets)
     (not (= c93954677_total_supply_at_construction c93954677_zero_supply))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
