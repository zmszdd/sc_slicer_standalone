; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c87168fd2_deposit_amount () Int)
(declare-fun c87168fd2_minted_shares () Int)
(declare-fun c87168fd2_total_assets_before () Int)
(declare-fun c87168fd2_total_supply_before () Int)
(assert
 (= c87168fd2_deposit_amount c87168fd2_deposit_amount))
(assert
 (= c87168fd2_minted_shares c87168fd2_minted_shares))
(assert
 (= c87168fd2_total_assets_before c87168fd2_total_assets_before))
(assert
 (= c87168fd2_total_supply_before c87168fd2_total_supply_before))
(define-fun report_preconditions () Bool (and (= 1 c87168fd2_total_supply_before)
     (= 1 c87168fd2_total_assets_before)
     (< 0 c87168fd2_deposit_amount)))
(define-fun report_safety () Bool (=> (< 0 c87168fd2_deposit_amount)
    (>= (* c87168fd2_minted_shares c87168fd2_total_assets_before)
        (* c87168fd2_deposit_amount c87168fd2_total_supply_before))))
(define-fun report_effects () Bool (and (< 0 c87168fd2_deposit_amount)
     (not (>= (* c87168fd2_minted_shares c87168fd2_total_assets_before)
              (* c87168fd2_deposit_amount c87168fd2_total_supply_before)))
     (< (* c87168fd2_minted_shares c87168fd2_total_assets_before)
        (* c87168fd2_deposit_amount c87168fd2_total_supply_before))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
