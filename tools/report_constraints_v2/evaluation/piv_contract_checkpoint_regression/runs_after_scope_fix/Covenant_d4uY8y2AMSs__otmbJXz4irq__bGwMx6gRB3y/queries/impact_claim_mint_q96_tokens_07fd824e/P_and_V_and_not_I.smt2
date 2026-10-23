; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2513dfd1_market_base_token_supply () Int)
(declare-fun c2513dfd1_mint_amount () Int)
(declare-fun c2513dfd1_minted_amount () Int)
(assert
 (= c2513dfd1_market_base_token_supply c2513dfd1_market_base_token_supply))
(assert
 (= c2513dfd1_mint_amount c2513dfd1_mint_amount))
(assert
 (= c2513dfd1_minted_amount c2513dfd1_minted_amount))
(define-fun report_preconditions () Bool (and (= 1000 c2513dfd1_market_base_token_supply)
     (= 79228162514264337593543950335 c2513dfd1_mint_amount)))
(define-fun report_safety () Bool (=> (> c2513dfd1_mint_amount c2513dfd1_market_base_token_supply)
    (= 0 c2513dfd1_minted_amount)))
(define-fun report_effects () Bool (and (> c2513dfd1_mint_amount c2513dfd1_market_base_token_supply)
     (not (= 0 c2513dfd1_minted_amount))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
