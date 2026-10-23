; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9941083e_first_mint_updates_twap () Bool)
(declare-fun c9941083e_followup_mint_possible () Bool)
(declare-fun c9941083e_last_etwap_base_supply () Int)
(declare-fun c9941083e_market_frozen_interim () Bool)
(assert
 (= c9941083e_first_mint_updates_twap c9941083e_first_mint_updates_twap))
(assert
 (= c9941083e_followup_mint_possible c9941083e_followup_mint_possible))
(assert
 (= c9941083e_last_etwap_base_supply c9941083e_last_etwap_base_supply))
(assert
 (= c9941083e_market_frozen_interim c9941083e_market_frozen_interim))
(define-fun report_preconditions () Bool (and (= 0 c9941083e_last_etwap_base_supply)
     (not c9941083e_first_mint_updates_twap)))
(define-fun report_safety () Bool (=> (and (= 0 c9941083e_last_etwap_base_supply)
         (not c9941083e_first_mint_updates_twap))
    (or c9941083e_followup_mint_possible (not c9941083e_market_frozen_interim))))
(define-fun report_effects () Bool (and (= 0 c9941083e_last_etwap_base_supply)
     (not c9941083e_first_mint_updates_twap)
     (not (or c9941083e_followup_mint_possible
              (not c9941083e_market_frozen_interim)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
