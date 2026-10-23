; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1781b8a9_bootstrap_shares_unallocated () Bool)
(declare-fun c1781b8a9_phantom_shares_present () Bool)
(declare-fun c1781b8a9_sum_of_balances () Int)
(declare-fun c1781b8a9_total_supply () Int)
(assert
 (= c1781b8a9_bootstrap_shares_unallocated c1781b8a9_bootstrap_shares_unallocated))
(assert
 (= c1781b8a9_phantom_shares_present c1781b8a9_phantom_shares_present))
(assert
 (= c1781b8a9_sum_of_balances c1781b8a9_sum_of_balances))
(assert
 (= c1781b8a9_total_supply c1781b8a9_total_supply))
(define-fun report_preconditions () Bool (and c1781b8a9_bootstrap_shares_unallocated c1781b8a9_phantom_shares_present))
(define-fun report_safety () Bool (=> c1781b8a9_bootstrap_shares_unallocated
    (= c1781b8a9_sum_of_balances c1781b8a9_total_supply)))
(define-fun report_effects () Bool (and c1781b8a9_bootstrap_shares_unallocated
     (not (= c1781b8a9_sum_of_balances c1781b8a9_total_supply))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
