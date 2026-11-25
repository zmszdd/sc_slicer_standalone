; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c05ef1a06_deposit_amount () Int)
(declare-fun c05ef1a06_minted_shares () Int)
(declare-fun c05ef1a06_total_assets_before () Int)
(declare-fun c05ef1a06_total_supply_before () Int)
(declare-fun c05ef1a06_zero_shares () Int)
(assert
 (= c05ef1a06_deposit_amount c05ef1a06_deposit_amount))
(assert
 (= c05ef1a06_minted_shares c05ef1a06_minted_shares))
(assert
 (= c05ef1a06_total_assets_before c05ef1a06_total_assets_before))
(assert
 (= c05ef1a06_total_supply_before c05ef1a06_total_supply_before))
(assert
 (= c05ef1a06_zero_shares c05ef1a06_zero_shares))
(define-fun report_preconditions () Bool (and (= 1 c05ef1a06_total_supply_before)
     (= 1 c05ef1a06_total_assets_before)
     (< 0 c05ef1a06_deposit_amount)))
(define-fun report_safety () Bool (=> (< 0 c05ef1a06_deposit_amount)
    (= (* c05ef1a06_minted_shares c05ef1a06_total_assets_before)
       (* c05ef1a06_deposit_amount c05ef1a06_total_supply_before))))
(define-fun report_effects () Bool (and (< 0 c05ef1a06_deposit_amount)
     (not (= (* c05ef1a06_minted_shares c05ef1a06_total_assets_before)
             (* c05ef1a06_deposit_amount c05ef1a06_total_supply_before)))
     (= c05ef1a06_minted_shares c05ef1a06_zero_shares)))
(assert report_preconditions)
(check-sat)
(get-model)
