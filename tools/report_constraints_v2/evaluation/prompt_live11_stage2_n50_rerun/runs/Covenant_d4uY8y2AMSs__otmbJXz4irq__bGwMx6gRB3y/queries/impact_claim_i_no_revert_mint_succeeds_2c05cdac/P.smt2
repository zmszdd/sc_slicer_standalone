; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8eeb34c3_market_base_token_supply () Int)
(declare-fun c8eeb34c3_mint_amount () Int)
(declare-fun c8eeb34c3_mint_reverted () Bool)
(declare-fun c8eeb34c3_q96 () Int)
(assert
 (= c8eeb34c3_market_base_token_supply c8eeb34c3_market_base_token_supply))
(assert
 (= c8eeb34c3_mint_amount c8eeb34c3_mint_amount))
(assert
 (= c8eeb34c3_mint_reverted c8eeb34c3_mint_reverted))
(assert
 (= c8eeb34c3_q96 c8eeb34c3_q96))
(define-fun report_preconditions () Bool (and (= c8eeb34c3_mint_amount c8eeb34c3_q96)
     (> c8eeb34c3_q96 c8eeb34c3_market_base_token_supply)))
(define-fun report_safety () Bool (=> (or (> c8eeb34c3_mint_amount c8eeb34c3_q96)
        (> c8eeb34c3_mint_amount c8eeb34c3_market_base_token_supply))
    c8eeb34c3_mint_reverted))
(define-fun report_effects () Bool (and (or (> c8eeb34c3_mint_amount c8eeb34c3_q96)
         (> c8eeb34c3_mint_amount c8eeb34c3_market_base_token_supply))
     (not c8eeb34c3_mint_reverted)))
(assert report_preconditions)
(check-sat)
(get-model)
