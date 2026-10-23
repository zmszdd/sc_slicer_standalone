; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca5533966_guard_passes_manipulated () Bool)
(declare-fun ca5533966_oracle_used_by_flows () Bool)
(declare-fun ca5533966_spot_price_manipulated () Bool)
(assert
 (= ca5533966_guard_passes_manipulated ca5533966_guard_passes_manipulated))
(assert
 (= ca5533966_oracle_used_by_flows ca5533966_oracle_used_by_flows))
(assert
 (= ca5533966_spot_price_manipulated ca5533966_spot_price_manipulated))
(define-fun report_preconditions () Bool (and ca5533966_spot_price_manipulated ca5533966_oracle_used_by_flows))
(define-fun report_safety () Bool (=> (and ca5533966_spot_price_manipulated ca5533966_oracle_used_by_flows)
    (not ca5533966_guard_passes_manipulated)))
(define-fun report_effects () Bool (and ca5533966_spot_price_manipulated
     ca5533966_oracle_used_by_flows
     (not (not ca5533966_guard_passes_manipulated))))
(assert report_preconditions)
(check-sat)
(get-model)
