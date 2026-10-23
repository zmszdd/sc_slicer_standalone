; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdb042868_first_mint_crosses_no_cap_limit () Bool)
(declare-fun cdb042868_follow_up_deposit_blocked () Bool)
(declare-fun cdb042868_last_etwap_base_supply_at_init () Int)
(assert
 (= cdb042868_first_mint_crosses_no_cap_limit cdb042868_first_mint_crosses_no_cap_limit))
(assert
 (= cdb042868_follow_up_deposit_blocked cdb042868_follow_up_deposit_blocked))
(assert
 (= cdb042868_last_etwap_base_supply_at_init cdb042868_last_etwap_base_supply_at_init))
(define-fun report_preconditions () Bool (and (= 0 cdb042868_last_etwap_base_supply_at_init)
     cdb042868_first_mint_crosses_no_cap_limit))
(define-fun report_safety () Bool (=> (and (= 0 cdb042868_last_etwap_base_supply_at_init)
         cdb042868_first_mint_crosses_no_cap_limit)
    (not cdb042868_follow_up_deposit_blocked)))
(define-fun report_effects () Bool (and (= 0 cdb042868_last_etwap_base_supply_at_init)
     cdb042868_first_mint_crosses_no_cap_limit
     (not (not cdb042868_follow_up_deposit_blocked))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
