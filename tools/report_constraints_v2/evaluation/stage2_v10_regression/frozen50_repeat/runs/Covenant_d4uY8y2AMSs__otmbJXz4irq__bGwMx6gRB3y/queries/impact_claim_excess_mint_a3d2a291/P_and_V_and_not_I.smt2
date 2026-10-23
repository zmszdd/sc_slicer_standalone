; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4b0e2a23_market_base_token_supply () Int)
(declare-fun c4b0e2a23_mint_amount () Int)
(declare-fun c4b0e2a23_minted_amount () Int)
(declare-fun c4b0e2a23_q96_cap () Int)
(assert
 (= c4b0e2a23_market_base_token_supply c4b0e2a23_market_base_token_supply))
(assert
 (= c4b0e2a23_mint_amount c4b0e2a23_mint_amount))
(assert
 (= c4b0e2a23_minted_amount c4b0e2a23_minted_amount))
(assert
 (= c4b0e2a23_q96_cap c4b0e2a23_q96_cap))
(define-fun report_preconditions () Bool (and (> c4b0e2a23_q96_cap c4b0e2a23_market_base_token_supply)
     (= c4b0e2a23_mint_amount c4b0e2a23_q96_cap)))
(define-fun report_safety () Bool (=> (and (> c4b0e2a23_q96_cap c4b0e2a23_market_base_token_supply)
         (= c4b0e2a23_mint_amount c4b0e2a23_q96_cap))
    (< c4b0e2a23_minted_amount c4b0e2a23_q96_cap)))
(define-fun report_effects () Bool (and (> c4b0e2a23_q96_cap c4b0e2a23_market_base_token_supply)
     (= c4b0e2a23_mint_amount c4b0e2a23_q96_cap)
     (not (< c4b0e2a23_minted_amount c4b0e2a23_q96_cap))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
