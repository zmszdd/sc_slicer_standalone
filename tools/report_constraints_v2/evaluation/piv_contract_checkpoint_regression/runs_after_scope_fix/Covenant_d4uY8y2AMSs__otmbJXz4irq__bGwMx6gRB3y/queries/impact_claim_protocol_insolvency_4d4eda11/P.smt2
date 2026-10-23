; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c206e056d_market_base_token_supply () Int)
(declare-fun c206e056d_mint_amount () Int)
(declare-fun c206e056d_synthetic_tokens_unbacked () Bool)
(assert
 (= c206e056d_market_base_token_supply c206e056d_market_base_token_supply))
(assert
 (= c206e056d_mint_amount c206e056d_mint_amount))
(assert
 (= c206e056d_synthetic_tokens_unbacked c206e056d_synthetic_tokens_unbacked))
(define-fun report_preconditions () Bool (and (= 1000 c206e056d_market_base_token_supply)
     (= 79228162514264337593543950335 c206e056d_mint_amount)))
(define-fun report_safety () Bool (=> (> c206e056d_mint_amount c206e056d_market_base_token_supply)
    (not c206e056d_synthetic_tokens_unbacked)))
(define-fun report_effects () Bool (and (> c206e056d_mint_amount c206e056d_market_base_token_supply)
     (not (not c206e056d_synthetic_tokens_unbacked))))
(assert report_preconditions)
(check-sat)
(get-model)
