; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cff0710d9_later_depositors_buy_worthless_shares () Bool)
(declare-fun cff0710d9_total_assets_before_first_fulfilment () Int)
(declare-fun cff0710d9_total_supply_at_construction () Int)
(declare-fun cff0710d9_vault_assets_at_construction () Int)
(declare-fun cff0710d9_zero_shares () Int)
(assert
 (= cff0710d9_later_depositors_buy_worthless_shares cff0710d9_later_depositors_buy_worthless_shares))
(assert
 (= cff0710d9_total_assets_before_first_fulfilment cff0710d9_total_assets_before_first_fulfilment))
(assert
 (= cff0710d9_total_supply_at_construction cff0710d9_total_supply_at_construction))
(assert
 (= cff0710d9_vault_assets_at_construction cff0710d9_vault_assets_at_construction))
(assert
 (= cff0710d9_zero_shares cff0710d9_zero_shares))
(define-fun report_preconditions () Bool (and (= 1000000 cff0710d9_total_supply_at_construction)
     (= 0 cff0710d9_vault_assets_at_construction)
     (= 1 cff0710d9_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> cff0710d9_later_depositors_buy_worthless_shares
    (=> (and (= 1000000 cff0710d9_total_supply_at_construction)
             (= 0 cff0710d9_vault_assets_at_construction)
             (= 1 cff0710d9_total_assets_before_first_fulfilment))
        (= cff0710d9_total_supply_at_construction cff0710d9_zero_shares))))
(define-fun report_effects () Bool (and cff0710d9_later_depositors_buy_worthless_shares
     (= 1000000 cff0710d9_total_supply_at_construction)
     (= 0 cff0710d9_vault_assets_at_construction)
     (= 1 cff0710d9_total_assets_before_first_fulfilment)
     (not (= cff0710d9_total_supply_at_construction cff0710d9_zero_shares))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
