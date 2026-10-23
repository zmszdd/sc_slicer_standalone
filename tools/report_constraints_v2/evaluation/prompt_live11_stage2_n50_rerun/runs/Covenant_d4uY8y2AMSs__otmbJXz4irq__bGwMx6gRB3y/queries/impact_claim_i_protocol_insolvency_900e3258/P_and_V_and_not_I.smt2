; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c33c749_market_base_token_supply () Int)
(declare-fun c4c33c749_mint_amount () Int)
(declare-fun c4c33c749_protocol_insolvent () Bool)
(declare-fun c4c33c749_q96_cap () Int)
(assert
 (= c4c33c749_market_base_token_supply c4c33c749_market_base_token_supply))
(assert
 (= c4c33c749_mint_amount c4c33c749_mint_amount))
(assert
 (= c4c33c749_protocol_insolvent c4c33c749_protocol_insolvent))
(assert
 (= c4c33c749_q96_cap c4c33c749_q96_cap))
(define-fun report_preconditions () Bool (and (= c4c33c749_mint_amount c4c33c749_q96_cap)
     (> c4c33c749_q96_cap c4c33c749_market_base_token_supply)))
(define-fun report_safety () Bool (=> (or (> c4c33c749_mint_amount c4c33c749_q96_cap)
        (> c4c33c749_mint_amount c4c33c749_market_base_token_supply))
    (not c4c33c749_protocol_insolvent)))
(define-fun report_effects () Bool (and (or (> c4c33c749_mint_amount c4c33c749_q96_cap)
         (> c4c33c749_mint_amount c4c33c749_market_base_token_supply))
     (not (not c4c33c749_protocol_insolvent))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
