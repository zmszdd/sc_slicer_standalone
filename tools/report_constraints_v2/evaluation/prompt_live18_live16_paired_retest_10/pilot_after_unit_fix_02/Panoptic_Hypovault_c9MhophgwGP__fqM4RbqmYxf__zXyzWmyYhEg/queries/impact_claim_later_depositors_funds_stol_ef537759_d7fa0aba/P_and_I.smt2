; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cff0710d9_later_depositors_buy_worthless_shares () Bool)
(declare-fun cff0710d9_total_supply_at_construction () Int)
(declare-fun cff0710d9_vault_underlying_assets_before_first_deposit () Int)
(declare-fun cff0710d9_zero_supply () Int)
(assert
 (= cff0710d9_later_depositors_buy_worthless_shares cff0710d9_later_depositors_buy_worthless_shares))
(assert
 (= cff0710d9_total_supply_at_construction cff0710d9_total_supply_at_construction))
(assert
 (= cff0710d9_vault_underlying_assets_before_first_deposit cff0710d9_vault_underlying_assets_before_first_deposit))
(assert
 (= cff0710d9_zero_supply cff0710d9_zero_supply))
(define-fun report_preconditions () Bool (and (= 1000000 cff0710d9_total_supply_at_construction)
     (= 0 cff0710d9_vault_underlying_assets_before_first_deposit)))
(define-fun report_safety () Bool (=> cff0710d9_later_depositors_buy_worthless_shares
    (=> (and (= 0 cff0710d9_vault_underlying_assets_before_first_deposit)
             (= 1000000 cff0710d9_total_supply_at_construction))
        (= cff0710d9_total_supply_at_construction cff0710d9_zero_supply))))
(define-fun report_effects () Bool (and cff0710d9_later_depositors_buy_worthless_shares
     (= 0 cff0710d9_vault_underlying_assets_before_first_deposit)
     (= 1000000 cff0710d9_total_supply_at_construction)
     (not (= cff0710d9_total_supply_at_construction cff0710d9_zero_supply))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
