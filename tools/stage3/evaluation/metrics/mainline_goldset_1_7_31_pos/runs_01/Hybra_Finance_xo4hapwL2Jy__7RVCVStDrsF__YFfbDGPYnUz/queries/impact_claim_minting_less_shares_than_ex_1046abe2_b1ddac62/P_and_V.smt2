; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3919c03e_deposit_amount () Int)
(declare-fun c3919c03e_minted_shares () Int)
(declare-fun c3919c03e_shares_less_than_expected () Bool)
(declare-fun c3919c03e_total_assets_before_deposit () Int)
(declare-fun c3919c03e_total_supply_before_deposit () Int)
(assert
 (= c3919c03e_deposit_amount c3919c03e_deposit_amount))
(assert
 (= c3919c03e_minted_shares c3919c03e_minted_shares))
(assert
 (= c3919c03e_shares_less_than_expected c3919c03e_shares_less_than_expected))
(assert
 (= c3919c03e_total_assets_before_deposit c3919c03e_total_assets_before_deposit))
(assert
 (= c3919c03e_total_supply_before_deposit c3919c03e_total_supply_before_deposit))
(define-fun report_preconditions () Bool (and (= 1 c3919c03e_total_supply_before_deposit)
     (= 1 c3919c03e_total_assets_before_deposit)
     (< 0 c3919c03e_deposit_amount)))
(define-fun report_safety () Bool (=> (and (= 1 c3919c03e_total_supply_before_deposit)
         (= 1 c3919c03e_total_assets_before_deposit)
         (< 0 c3919c03e_deposit_amount))
    (>= (* c3919c03e_minted_shares c3919c03e_total_assets_before_deposit)
        (* c3919c03e_deposit_amount c3919c03e_total_supply_before_deposit))))
(define-fun report_effects () Bool (and (= 1 c3919c03e_total_supply_before_deposit)
     (= 1 c3919c03e_total_assets_before_deposit)
     (< 0 c3919c03e_deposit_amount)
     (not (>= (* c3919c03e_minted_shares c3919c03e_total_assets_before_deposit)
              (* c3919c03e_deposit_amount c3919c03e_total_supply_before_deposit)))
     c3919c03e_shares_less_than_expected))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
