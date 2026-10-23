; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cff0710d9_later_depositors_bought_worthless_shares () Bool)
(declare-fun cff0710d9_shares_minted_without_assets () Bool)
(declare-fun cff0710d9_total_supply_at_bootstrap () Int)
(declare-fun cff0710d9_underlying_assets_at_bootstrap () Int)
(declare-fun cff0710d9_zero_assets () Int)
(assert
 (= cff0710d9_later_depositors_bought_worthless_shares cff0710d9_later_depositors_bought_worthless_shares))
(assert
 (= cff0710d9_shares_minted_without_assets cff0710d9_shares_minted_without_assets))
(assert
 (= cff0710d9_total_supply_at_bootstrap cff0710d9_total_supply_at_bootstrap))
(assert
 (= cff0710d9_underlying_assets_at_bootstrap cff0710d9_underlying_assets_at_bootstrap))
(assert
 (= cff0710d9_zero_assets cff0710d9_zero_assets))
(define-fun report_preconditions () Bool (and (= 1000000 cff0710d9_total_supply_at_bootstrap)
     (= cff0710d9_underlying_assets_at_bootstrap cff0710d9_zero_assets)))
(define-fun report_safety () Bool (=> cff0710d9_later_depositors_bought_worthless_shares
    (=> (= cff0710d9_underlying_assets_at_bootstrap cff0710d9_zero_assets)
        (= cff0710d9_shares_minted_without_assets
           cff0710d9_later_depositors_bought_worthless_shares))))
(define-fun report_effects () Bool (and cff0710d9_later_depositors_bought_worthless_shares
     (= cff0710d9_underlying_assets_at_bootstrap cff0710d9_zero_assets)
     (not (= cff0710d9_shares_minted_without_assets
             cff0710d9_later_depositors_bought_worthless_shares))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
