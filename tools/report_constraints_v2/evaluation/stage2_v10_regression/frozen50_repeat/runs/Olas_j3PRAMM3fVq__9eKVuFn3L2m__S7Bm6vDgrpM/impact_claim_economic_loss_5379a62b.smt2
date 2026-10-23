; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c143d1f_manipulated_spot_rejected () Bool)
(declare-fun c4c143d1f_protocol_funds_economically_lost () Bool)
(declare-fun c4c143d1f_spot_price_manipulated () Bool)
(declare-fun c4c143d1f_twap_from_historical_cumulative () Bool)
(assert
 (= c4c143d1f_manipulated_spot_rejected c4c143d1f_manipulated_spot_rejected))
(assert
 (= c4c143d1f_protocol_funds_economically_lost c4c143d1f_protocol_funds_economically_lost))
(assert
 (= c4c143d1f_spot_price_manipulated c4c143d1f_spot_price_manipulated))
(assert
 (= c4c143d1f_twap_from_historical_cumulative c4c143d1f_twap_from_historical_cumulative))
(define-fun report_preconditions () Bool c4c143d1f_spot_price_manipulated)
(define-fun report_safety () Bool (=> c4c143d1f_spot_price_manipulated
    (and c4c143d1f_twap_from_historical_cumulative
         c4c143d1f_manipulated_spot_rejected
         (not c4c143d1f_protocol_funds_economically_lost))))
(define-fun report_effects () Bool (and c4c143d1f_spot_price_manipulated
     (not (and c4c143d1f_twap_from_historical_cumulative
               c4c143d1f_manipulated_spot_rejected
               (not c4c143d1f_protocol_funds_economically_lost)))))
