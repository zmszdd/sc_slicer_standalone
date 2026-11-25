; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6a22486d_bootstrap_shares () Int)
(declare-fun c6a22486d_total_supply_shares () Int)
(declare-fun c6a22486d_unowned_shares_in_supply () Bool)
(declare-fun c6a22486d_vault_value_stolen_by_phantom_shares () Bool)
(assert
 (= c6a22486d_bootstrap_shares c6a22486d_bootstrap_shares))
(assert
 (= c6a22486d_total_supply_shares c6a22486d_total_supply_shares))
(assert
 (= c6a22486d_unowned_shares_in_supply c6a22486d_unowned_shares_in_supply))
(assert
 (= c6a22486d_vault_value_stolen_by_phantom_shares c6a22486d_vault_value_stolen_by_phantom_shares))
(define-fun report_preconditions () Bool (and (= c6a22486d_total_supply_shares c6a22486d_bootstrap_shares)
     c6a22486d_unowned_shares_in_supply))
(define-fun report_safety () Bool (=> (= 1000000 c6a22486d_bootstrap_shares)
    (=> c6a22486d_unowned_shares_in_supply
        (not c6a22486d_unowned_shares_in_supply))))
(define-fun report_effects () Bool (and (= 1000000 c6a22486d_bootstrap_shares)
     c6a22486d_unowned_shares_in_supply
     c6a22486d_unowned_shares_in_supply
     c6a22486d_vault_value_stolen_by_phantom_shares))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
