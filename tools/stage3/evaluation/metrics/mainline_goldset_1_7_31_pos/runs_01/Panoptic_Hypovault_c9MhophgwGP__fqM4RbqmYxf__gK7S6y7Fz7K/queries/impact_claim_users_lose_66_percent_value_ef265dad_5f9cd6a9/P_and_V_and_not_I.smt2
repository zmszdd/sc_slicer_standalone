; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c538c9ab7_bootstrap_shares_allocated () Bool)
(declare-fun c538c9ab7_bootstrap_shares_owned () Bool)
(declare-fun c538c9ab7_sum_of_balances_shares () Int)
(declare-fun c538c9ab7_total_supply_shares () Int)
(declare-fun c538c9ab7_user_value_loss_percent () Int)
(assert
 (= c538c9ab7_bootstrap_shares_allocated c538c9ab7_bootstrap_shares_allocated))
(assert
 (= c538c9ab7_bootstrap_shares_owned c538c9ab7_bootstrap_shares_owned))
(assert
 (= c538c9ab7_sum_of_balances_shares c538c9ab7_sum_of_balances_shares))
(assert
 (= c538c9ab7_total_supply_shares c538c9ab7_total_supply_shares))
(assert
 (= c538c9ab7_user_value_loss_percent c538c9ab7_user_value_loss_percent))
(define-fun report_preconditions () Bool (and (not c538c9ab7_bootstrap_shares_allocated)
     (not c538c9ab7_bootstrap_shares_owned)))
(define-fun report_safety () Bool (=> (not c538c9ab7_bootstrap_shares_allocated)
    (= c538c9ab7_total_supply_shares c538c9ab7_sum_of_balances_shares)))
(define-fun report_effects () Bool (and (not c538c9ab7_bootstrap_shares_allocated)
     (not (= c538c9ab7_total_supply_shares c538c9ab7_sum_of_balances_shares))
     (= 66 c538c9ab7_user_value_loss_percent)
     (= 66 c538c9ab7_user_value_loss_percent)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
