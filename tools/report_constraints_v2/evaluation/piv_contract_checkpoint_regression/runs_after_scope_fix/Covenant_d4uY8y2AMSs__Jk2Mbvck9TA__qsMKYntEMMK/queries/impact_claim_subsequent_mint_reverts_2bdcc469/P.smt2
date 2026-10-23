; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc5de1dc1_first_mint_crosses_no_cap_limit () Bool)
(declare-fun cc5de1dc1_last_etwap_base_supply_at_init () Int)
(declare-fun cc5de1dc1_subsequent_mint_reverted () Bool)
(assert
 (= cc5de1dc1_first_mint_crosses_no_cap_limit cc5de1dc1_first_mint_crosses_no_cap_limit))
(assert
 (= cc5de1dc1_last_etwap_base_supply_at_init cc5de1dc1_last_etwap_base_supply_at_init))
(assert
 (= cc5de1dc1_subsequent_mint_reverted cc5de1dc1_subsequent_mint_reverted))
(define-fun report_preconditions () Bool (and (= 0 cc5de1dc1_last_etwap_base_supply_at_init)
     cc5de1dc1_first_mint_crosses_no_cap_limit))
(define-fun report_safety () Bool (=> (and (= 0 cc5de1dc1_last_etwap_base_supply_at_init)
         cc5de1dc1_first_mint_crosses_no_cap_limit)
    (not cc5de1dc1_subsequent_mint_reverted)))
(define-fun report_effects () Bool (and (= 0 cc5de1dc1_last_etwap_base_supply_at_init)
     cc5de1dc1_first_mint_crosses_no_cap_limit
     (not (not cc5de1dc1_subsequent_mint_reverted))))
(assert report_preconditions)
(check-sat)
(get-model)
