; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c982419af_market_base_token_supply () Int)
(declare-fun c982419af_mint_amount () Int)
(declare-fun c982419af_mint_cap_exceeded () Bool)
(declare-fun c982419af_q96_cap () Int)
(declare-fun c982419af_tokens_minted () Int)
(assert
 (= c982419af_market_base_token_supply c982419af_market_base_token_supply))
(assert
 (= c982419af_mint_amount c982419af_mint_amount))
(assert
 (= c982419af_mint_cap_exceeded c982419af_mint_cap_exceeded))
(assert
 (= c982419af_q96_cap c982419af_q96_cap))
(assert
 (= c982419af_tokens_minted c982419af_tokens_minted))
(define-fun report_preconditions () Bool (and (= c982419af_mint_amount c982419af_q96_cap)
     (> c982419af_q96_cap c982419af_market_base_token_supply)))
(define-fun report_safety () Bool (=> (or (> c982419af_mint_amount c982419af_q96_cap)
        (> c982419af_mint_amount c982419af_market_base_token_supply))
    (and (<= c982419af_tokens_minted c982419af_q96_cap)
         (not c982419af_mint_cap_exceeded))))
(define-fun report_effects () Bool (and (or (> c982419af_mint_amount c982419af_q96_cap)
         (> c982419af_mint_amount c982419af_market_base_token_supply))
     (not (and (<= c982419af_tokens_minted c982419af_q96_cap)
               (not c982419af_mint_cap_exceeded)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
