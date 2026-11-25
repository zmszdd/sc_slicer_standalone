; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0f97899b_later_deposit_amount () Int)
(declare-fun c0f97899b_minted_shares () Int)
(declare-fun c0f97899b_total_assets_seed () Int)
(declare-fun c0f97899b_total_supply_seed () Int)
(declare-fun c0f97899b_value_transferred_to_holders () Bool)
(assert
 (= c0f97899b_later_deposit_amount c0f97899b_later_deposit_amount))
(assert
 (= c0f97899b_minted_shares c0f97899b_minted_shares))
(assert
 (= c0f97899b_total_assets_seed c0f97899b_total_assets_seed))
(assert
 (= c0f97899b_total_supply_seed c0f97899b_total_supply_seed))
(assert
 (= c0f97899b_value_transferred_to_holders c0f97899b_value_transferred_to_holders))
(define-fun report_preconditions () Bool (and (= 1 c0f97899b_total_supply_seed)
     (= 1 c0f97899b_total_assets_seed)
     (< 0 c0f97899b_later_deposit_amount)))
(define-fun report_safety () Bool (=> (< 0 c0f97899b_later_deposit_amount)
    (>= (* c0f97899b_minted_shares
           (+ c0f97899b_total_assets_seed c0f97899b_later_deposit_amount))
        (* c0f97899b_later_deposit_amount c0f97899b_total_supply_seed))))
(define-fun report_effects () Bool (let ((a!1 (not (>= (* c0f97899b_minted_shares
                       (+ c0f97899b_total_assets_seed
                          c0f97899b_later_deposit_amount))
                    (* c0f97899b_later_deposit_amount
                       c0f97899b_total_supply_seed)))))
  (and (< 0 c0f97899b_later_deposit_amount)
       a!1
       c0f97899b_value_transferred_to_holders)))
