; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c973a10c1_later_depositor_funds_stolen () Bool)
(declare-fun c973a10c1_shares_minted_without_assets () Bool)
(declare-fun c973a10c1_total_supply_at_bootstrap () Int)
(declare-fun c973a10c1_underlying_assets_at_bootstrap () Int)
(assert
 (= c973a10c1_later_depositor_funds_stolen c973a10c1_later_depositor_funds_stolen))
(assert
 (= c973a10c1_shares_minted_without_assets c973a10c1_shares_minted_without_assets))
(assert
 (= c973a10c1_total_supply_at_bootstrap c973a10c1_total_supply_at_bootstrap))
(assert
 (= c973a10c1_underlying_assets_at_bootstrap c973a10c1_underlying_assets_at_bootstrap))
(define-fun report_preconditions () Bool (and (= 1000000 c973a10c1_total_supply_at_bootstrap)
     (= 0 c973a10c1_underlying_assets_at_bootstrap)))
(define-fun report_safety () Bool (=> c973a10c1_later_depositor_funds_stolen
    (=> (and (= 1000000 c973a10c1_total_supply_at_bootstrap)
             (= 0 c973a10c1_underlying_assets_at_bootstrap))
        (= c973a10c1_shares_minted_without_assets
           c973a10c1_later_depositor_funds_stolen))))
(define-fun report_effects () Bool (and c973a10c1_later_depositor_funds_stolen
     (= 1000000 c973a10c1_total_supply_at_bootstrap)
     (= 0 c973a10c1_underlying_assets_at_bootstrap)
     (not (= c973a10c1_shares_minted_without_assets
             c973a10c1_later_depositor_funds_stolen))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
