; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0cb03190_adapter_chain_configured () Bool)
(declare-fun c0cb03190_inverse_direction_call () Bool)
(declare-fun c0cb03190_prices_updated () Bool)
(assert
 (= c0cb03190_adapter_chain_configured c0cb03190_adapter_chain_configured))
(assert
 (= c0cb03190_inverse_direction_call c0cb03190_inverse_direction_call))
(assert
 (= c0cb03190_prices_updated c0cb03190_prices_updated))
(define-fun report_preconditions () Bool (and c0cb03190_inverse_direction_call c0cb03190_adapter_chain_configured))
(define-fun report_safety () Bool (=> (and c0cb03190_inverse_direction_call c0cb03190_adapter_chain_configured)
    c0cb03190_prices_updated))
(define-fun report_effects () Bool (and c0cb03190_inverse_direction_call
     c0cb03190_adapter_chain_configured
     (not c0cb03190_prices_updated)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
