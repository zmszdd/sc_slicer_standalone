; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cede7b611_balance_ () Int)
(declare-fun cede7b611_balance_reduced_by_defi_mechanism () Bool)
(declare-fun cede7b611_distribute_rewards_call_succeeds () Bool)
(declare-fun cede7b611_last_underlying_balance () Int)
(assert
 (= cede7b611_balance_ cede7b611_balance_))
(assert
 (= cede7b611_balance_reduced_by_defi_mechanism cede7b611_balance_reduced_by_defi_mechanism))
(assert
 (= cede7b611_distribute_rewards_call_succeeds cede7b611_distribute_rewards_call_succeeds))
(assert
 (= cede7b611_last_underlying_balance cede7b611_last_underlying_balance))
(define-fun report_preconditions () Bool (and (< cede7b611_balance_ cede7b611_last_underlying_balance)
     cede7b611_balance_reduced_by_defi_mechanism))
(define-fun report_safety () Bool (=> (and (< cede7b611_balance_ cede7b611_last_underlying_balance)
         cede7b611_balance_reduced_by_defi_mechanism)
    cede7b611_distribute_rewards_call_succeeds))
(define-fun report_effects () Bool (and (< cede7b611_balance_ cede7b611_last_underlying_balance)
     cede7b611_balance_reduced_by_defi_mechanism
     (not cede7b611_distribute_rewards_call_succeeds)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
