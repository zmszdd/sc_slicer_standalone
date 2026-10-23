; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c31f81b99_first_mint_updates_twap () Bool)
(declare-fun c31f81b99_last_etwap_base_supply () Int)
(declare-fun c31f81b99_subsequent_mint_reverts_cap_exceeded () Bool)
(assert
 (= c31f81b99_first_mint_updates_twap c31f81b99_first_mint_updates_twap))
(assert
 (= c31f81b99_last_etwap_base_supply c31f81b99_last_etwap_base_supply))
(assert
 (= c31f81b99_subsequent_mint_reverts_cap_exceeded c31f81b99_subsequent_mint_reverts_cap_exceeded))
(define-fun report_preconditions () Bool (and (= 0 c31f81b99_last_etwap_base_supply)
     (not c31f81b99_first_mint_updates_twap)))
(define-fun report_safety () Bool (=> (and (= 0 c31f81b99_last_etwap_base_supply)
         (not c31f81b99_first_mint_updates_twap))
    (not c31f81b99_subsequent_mint_reverts_cap_exceeded)))
(define-fun report_effects () Bool (and (= 0 c31f81b99_last_etwap_base_supply)
     (not c31f81b99_first_mint_updates_twap)
     (not (not c31f81b99_subsequent_mint_reverts_cap_exceeded))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
