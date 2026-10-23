; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c589b355c_market_base_token_supply () Int)
(declare-fun c589b355c_mint_amount () Int)
(declare-fun c589b355c_mint_succeeds () Bool)
(assert
 (= c589b355c_market_base_token_supply c589b355c_market_base_token_supply))
(assert
 (= c589b355c_mint_amount c589b355c_mint_amount))
(assert
 (= c589b355c_mint_succeeds c589b355c_mint_succeeds))
(define-fun report_preconditions () Bool (and (= 1000 c589b355c_market_base_token_supply)
     (= 79228162514264337593543950335 c589b355c_mint_amount)))
(define-fun report_safety () Bool (=> (> c589b355c_mint_amount c589b355c_market_base_token_supply)
    (not c589b355c_mint_succeeds)))
(define-fun report_effects () Bool (and (> c589b355c_mint_amount c589b355c_market_base_token_supply)
     (not (not c589b355c_mint_succeeds))))
