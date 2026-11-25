; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfcfa2b92_later_deposit_amount () Int)
(declare-fun cfcfa2b92_minted_shares_observed () Int)
(declare-fun cfcfa2b92_total_assets_seed () Int)
(declare-fun cfcfa2b92_total_supply_seed () Int)
(assert
 (= cfcfa2b92_later_deposit_amount cfcfa2b92_later_deposit_amount))
(assert
 (= cfcfa2b92_minted_shares_observed cfcfa2b92_minted_shares_observed))
(assert
 (= cfcfa2b92_total_assets_seed cfcfa2b92_total_assets_seed))
(assert
 (= cfcfa2b92_total_supply_seed cfcfa2b92_total_supply_seed))
(define-fun report_preconditions () Bool (and (= 1 cfcfa2b92_total_supply_seed)
     (= 1 cfcfa2b92_total_assets_seed)
     (< 0 cfcfa2b92_later_deposit_amount)))
(define-fun report_safety () Bool (=> (< 0 cfcfa2b92_later_deposit_amount)
    (>= (* cfcfa2b92_minted_shares_observed cfcfa2b92_total_assets_seed)
        (* cfcfa2b92_later_deposit_amount cfcfa2b92_total_supply_seed))))
(define-fun report_effects () Bool (and (< 0 cfcfa2b92_later_deposit_amount)
     (not (>= (* cfcfa2b92_minted_shares_observed cfcfa2b92_total_assets_seed)
              (* cfcfa2b92_later_deposit_amount cfcfa2b92_total_supply_seed)))
     (< (* cfcfa2b92_minted_shares_observed cfcfa2b92_total_assets_seed)
        (* cfcfa2b92_later_deposit_amount cfcfa2b92_total_supply_seed))))
