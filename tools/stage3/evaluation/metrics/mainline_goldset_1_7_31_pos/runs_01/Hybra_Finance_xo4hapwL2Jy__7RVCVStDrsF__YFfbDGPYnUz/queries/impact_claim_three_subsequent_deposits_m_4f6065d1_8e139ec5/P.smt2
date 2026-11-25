; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c8b8620_later_deposit_amount () Int)
(declare-fun c9c8b8620_minted_shares () Int)
(declare-fun c9c8b8620_subsequent_deposit_count () Int)
(declare-fun c9c8b8620_total_assets_seed () Int)
(declare-fun c9c8b8620_total_supply_seed () Int)
(declare-fun c9c8b8620_zero_shares () Int)
(assert
 (= c9c8b8620_later_deposit_amount c9c8b8620_later_deposit_amount))
(assert
 (= c9c8b8620_minted_shares c9c8b8620_minted_shares))
(assert
 (= c9c8b8620_subsequent_deposit_count c9c8b8620_subsequent_deposit_count))
(assert
 (= c9c8b8620_total_assets_seed c9c8b8620_total_assets_seed))
(assert
 (= c9c8b8620_total_supply_seed c9c8b8620_total_supply_seed))
(assert
 (= c9c8b8620_zero_shares c9c8b8620_zero_shares))
(define-fun report_preconditions () Bool (and (= 1 c9c8b8620_total_supply_seed)
     (= 1 c9c8b8620_total_assets_seed)
     (< 0 c9c8b8620_later_deposit_amount)))
(define-fun report_safety () Bool (=> (< 0 c9c8b8620_later_deposit_amount)
    (= (* c9c8b8620_minted_shares c9c8b8620_total_assets_seed)
       (* c9c8b8620_later_deposit_amount c9c8b8620_total_supply_seed))))
(define-fun report_effects () Bool (and (< 0 c9c8b8620_later_deposit_amount)
     (not (= (* c9c8b8620_minted_shares c9c8b8620_total_assets_seed)
             (* c9c8b8620_later_deposit_amount c9c8b8620_total_supply_seed)))
     (= c9c8b8620_minted_shares c9c8b8620_zero_shares)
     (= 3 c9c8b8620_subsequent_deposit_count)
     (= 3 c9c8b8620_subsequent_deposit_count)))
(assert report_preconditions)
(check-sat)
(get-model)
