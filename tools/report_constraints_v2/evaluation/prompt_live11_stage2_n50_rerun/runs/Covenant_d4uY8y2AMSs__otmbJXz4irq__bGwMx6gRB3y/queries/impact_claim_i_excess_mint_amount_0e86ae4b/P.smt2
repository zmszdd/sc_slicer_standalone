; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c47bca965_market_base_token_supply () Int)
(declare-fun c47bca965_mint_amount () Int)
(declare-fun c47bca965_mint_reverted () Bool)
(declare-fun c47bca965_q96_cap () Int)
(assert
 (= c47bca965_market_base_token_supply c47bca965_market_base_token_supply))
(assert
 (= c47bca965_mint_amount c47bca965_mint_amount))
(assert
 (= c47bca965_mint_reverted c47bca965_mint_reverted))
(assert
 (= c47bca965_q96_cap c47bca965_q96_cap))
(define-fun report_preconditions () Bool (and (= c47bca965_mint_amount c47bca965_q96_cap)
     (> c47bca965_q96_cap c47bca965_market_base_token_supply)))
(define-fun report_safety () Bool (=> (or (> c47bca965_mint_amount c47bca965_q96_cap)
        (> c47bca965_mint_amount c47bca965_market_base_token_supply))
    c47bca965_mint_reverted))
(define-fun report_effects () Bool (and (or (> c47bca965_mint_amount c47bca965_q96_cap)
         (> c47bca965_mint_amount c47bca965_market_base_token_supply))
     (not c47bca965_mint_reverted)))
(assert report_preconditions)
(check-sat)
(get-model)
