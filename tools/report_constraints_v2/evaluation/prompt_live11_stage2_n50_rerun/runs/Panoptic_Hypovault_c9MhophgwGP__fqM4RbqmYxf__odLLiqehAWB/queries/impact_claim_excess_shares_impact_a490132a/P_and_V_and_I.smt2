; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cba6a368f_deposit_assets () Int)
(declare-fun cba6a368f_share_backing_ratio_ok () Bool)
(declare-fun cba6a368f_sum_of_balances () Int)
(declare-fun cba6a368f_total_supply_preset_value () Int)
(assert
 (= cba6a368f_deposit_assets cba6a368f_deposit_assets))
(assert
 (= cba6a368f_share_backing_ratio_ok cba6a368f_share_backing_ratio_ok))
(assert
 (= cba6a368f_sum_of_balances cba6a368f_sum_of_balances))
(assert
 (= cba6a368f_total_supply_preset_value cba6a368f_total_supply_preset_value))
(define-fun report_preconditions () Bool (and (= 1000000 cba6a368f_total_supply_preset_value)
     (= 0 cba6a368f_sum_of_balances)
     (= 1000 cba6a368f_deposit_assets)))
(define-fun report_safety () Bool (=> (and (= 1000000 cba6a368f_total_supply_preset_value)
         (= 0 cba6a368f_sum_of_balances)
         (= 1000 cba6a368f_deposit_assets))
    cba6a368f_share_backing_ratio_ok))
(define-fun report_effects () Bool (and (= 1000000 cba6a368f_total_supply_preset_value)
     (= 0 cba6a368f_sum_of_balances)
     (= 1000 cba6a368f_deposit_assets)
     (not cba6a368f_share_backing_ratio_ok)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
