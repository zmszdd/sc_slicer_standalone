; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c52776f2e_bootstrap_shares_amount () Int)
(declare-fun c52776f2e_bootstrap_shares_owned () Bool)
(declare-fun c52776f2e_sum_of_balances_shares () Int)
(declare-fun c52776f2e_total_supply_shares () Int)
(declare-fun c52776f2e_vault_value_stolen () Bool)
(assert
 (= c52776f2e_bootstrap_shares_amount c52776f2e_bootstrap_shares_amount))
(assert
 (= c52776f2e_bootstrap_shares_owned c52776f2e_bootstrap_shares_owned))
(assert
 (= c52776f2e_sum_of_balances_shares c52776f2e_sum_of_balances_shares))
(assert
 (= c52776f2e_total_supply_shares c52776f2e_total_supply_shares))
(assert
 (= c52776f2e_vault_value_stolen c52776f2e_vault_value_stolen))
(define-fun report_preconditions () Bool (and (= c52776f2e_total_supply_shares c52776f2e_bootstrap_shares_amount)
     (not c52776f2e_bootstrap_shares_owned)))
(define-fun report_safety () Bool (=> (not c52776f2e_bootstrap_shares_owned)
    (= c52776f2e_sum_of_balances_shares c52776f2e_total_supply_shares)))
(define-fun report_effects () Bool (and (not c52776f2e_bootstrap_shares_owned)
     (not (= c52776f2e_sum_of_balances_shares c52776f2e_total_supply_shares))
     c52776f2e_vault_value_stolen))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
