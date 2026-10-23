; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca5533966_guard_passes_manipulated_price () Bool)
(declare-fun ca5533966_oracle_used_as_slippage_guard () Bool)
(declare-fun ca5533966_spot_price_manipulated () Bool)
(assert
 (= ca5533966_guard_passes_manipulated_price ca5533966_guard_passes_manipulated_price))
(assert
 (= ca5533966_oracle_used_as_slippage_guard ca5533966_oracle_used_as_slippage_guard))
(assert
 (= ca5533966_spot_price_manipulated ca5533966_spot_price_manipulated))
(define-fun report_preconditions () Bool (and ca5533966_spot_price_manipulated ca5533966_oracle_used_as_slippage_guard))
(define-fun report_safety () Bool (=> (and ca5533966_spot_price_manipulated
         ca5533966_oracle_used_as_slippage_guard)
    (not ca5533966_guard_passes_manipulated_price)))
(define-fun report_effects () Bool (and ca5533966_spot_price_manipulated
     ca5533966_oracle_used_as_slippage_guard
     (not (not ca5533966_guard_passes_manipulated_price))))
