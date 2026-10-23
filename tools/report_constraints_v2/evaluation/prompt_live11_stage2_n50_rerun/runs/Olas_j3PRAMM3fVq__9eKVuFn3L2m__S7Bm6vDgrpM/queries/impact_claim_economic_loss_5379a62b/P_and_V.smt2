; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c143d1f_economic_loss_occurs () Bool)
(declare-fun c4c143d1f_guard_rejects_manipulated_price () Bool)
(declare-fun c4c143d1f_guard_used_for_flows () Bool)
(declare-fun c4c143d1f_spot_price_manipulable () Bool)
(assert
 (= c4c143d1f_economic_loss_occurs c4c143d1f_economic_loss_occurs))
(assert
 (= c4c143d1f_guard_rejects_manipulated_price c4c143d1f_guard_rejects_manipulated_price))
(assert
 (= c4c143d1f_guard_used_for_flows c4c143d1f_guard_used_for_flows))
(assert
 (= c4c143d1f_spot_price_manipulable c4c143d1f_spot_price_manipulable))
(define-fun report_preconditions () Bool (and c4c143d1f_spot_price_manipulable c4c143d1f_guard_used_for_flows))
(define-fun report_safety () Bool (=> (and c4c143d1f_spot_price_manipulable c4c143d1f_guard_used_for_flows)
    (and c4c143d1f_guard_rejects_manipulated_price
         (not c4c143d1f_economic_loss_occurs))))
(define-fun report_effects () Bool (and c4c143d1f_spot_price_manipulable
     c4c143d1f_guard_used_for_flows
     (not (and c4c143d1f_guard_rejects_manipulated_price
               (not c4c143d1f_economic_loss_occurs)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
