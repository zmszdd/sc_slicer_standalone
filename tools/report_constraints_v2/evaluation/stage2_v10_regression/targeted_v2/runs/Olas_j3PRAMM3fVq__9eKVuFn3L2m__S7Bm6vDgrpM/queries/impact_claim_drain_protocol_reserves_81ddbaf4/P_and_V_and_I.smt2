; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c373b84bb_guard_rejects_manipulated_price () Bool)
(declare-fun c373b84bb_protocol_reserves_drained () Bool)
(declare-fun c373b84bb_spot_price_manipulable () Bool)
(assert
 (= c373b84bb_guard_rejects_manipulated_price c373b84bb_guard_rejects_manipulated_price))
(assert
 (= c373b84bb_protocol_reserves_drained c373b84bb_protocol_reserves_drained))
(assert
 (= c373b84bb_spot_price_manipulable c373b84bb_spot_price_manipulable))
(define-fun report_preconditions () Bool c373b84bb_spot_price_manipulable)
(define-fun report_safety () Bool (=> c373b84bb_spot_price_manipulable
    (and c373b84bb_guard_rejects_manipulated_price
         (not c373b84bb_protocol_reserves_drained))))
(define-fun report_effects () Bool (and c373b84bb_spot_price_manipulable
     (not (and c373b84bb_guard_rejects_manipulated_price
               (not c373b84bb_protocol_reserves_drained)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
