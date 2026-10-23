; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd09bf263_balance_ () Int)
(declare-fun cd09bf263_balance_reduced_by_defi_mechanism () Bool)
(declare-fun cd09bf263_last_underlying_balance () Int)
(declare-fun cd09bf263_reward_distribution_fails_for_all_users () Bool)
(assert
 (= cd09bf263_balance_ cd09bf263_balance_))
(assert
 (= cd09bf263_balance_reduced_by_defi_mechanism cd09bf263_balance_reduced_by_defi_mechanism))
(assert
 (= cd09bf263_last_underlying_balance cd09bf263_last_underlying_balance))
(assert
 (= cd09bf263_reward_distribution_fails_for_all_users cd09bf263_reward_distribution_fails_for_all_users))
(define-fun report_preconditions () Bool (and (< cd09bf263_balance_ cd09bf263_last_underlying_balance)
     cd09bf263_balance_reduced_by_defi_mechanism))
(define-fun report_safety () Bool (=> (and (< cd09bf263_balance_ cd09bf263_last_underlying_balance)
         cd09bf263_balance_reduced_by_defi_mechanism)
    (not cd09bf263_reward_distribution_fails_for_all_users)))
(define-fun report_effects () Bool (and (< cd09bf263_balance_ cd09bf263_last_underlying_balance)
     cd09bf263_balance_reduced_by_defi_mechanism
     (not (not cd09bf263_reward_distribution_fails_for_all_users))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
