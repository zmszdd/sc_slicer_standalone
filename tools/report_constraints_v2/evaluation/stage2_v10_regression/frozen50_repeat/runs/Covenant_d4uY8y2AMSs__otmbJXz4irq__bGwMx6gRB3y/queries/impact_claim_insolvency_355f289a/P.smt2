; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2c8b5168_market_base_token_supply () Int)
(declare-fun c2c8b5168_mint_amount () Int)
(declare-fun c2c8b5168_mint_succeeds () Bool)
(declare-fun c2c8b5168_protocol_insolvent () Bool)
(declare-fun c2c8b5168_q96 () Int)
(assert
 (= c2c8b5168_market_base_token_supply c2c8b5168_market_base_token_supply))
(assert
 (= c2c8b5168_mint_amount c2c8b5168_mint_amount))
(assert
 (= c2c8b5168_mint_succeeds c2c8b5168_mint_succeeds))
(assert
 (= c2c8b5168_protocol_insolvent c2c8b5168_protocol_insolvent))
(assert
 (= c2c8b5168_q96 c2c8b5168_q96))
(define-fun report_preconditions () Bool (and (> c2c8b5168_q96 c2c8b5168_market_base_token_supply)
     (= c2c8b5168_mint_amount c2c8b5168_q96)))
(define-fun report_safety () Bool (=> (and (> c2c8b5168_q96 c2c8b5168_market_base_token_supply)
         (= c2c8b5168_mint_amount c2c8b5168_q96))
    (and (not c2c8b5168_mint_succeeds) (not c2c8b5168_protocol_insolvent))))
(define-fun report_effects () Bool (and (> c2c8b5168_q96 c2c8b5168_market_base_token_supply)
     (= c2c8b5168_mint_amount c2c8b5168_q96)
     (not (and (not c2c8b5168_mint_succeeds) (not c2c8b5168_protocol_insolvent)))))
(assert report_preconditions)
(check-sat)
(get-model)
