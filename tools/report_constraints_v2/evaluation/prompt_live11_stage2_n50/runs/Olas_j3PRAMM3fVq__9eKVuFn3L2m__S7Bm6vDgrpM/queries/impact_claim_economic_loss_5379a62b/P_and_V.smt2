; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c143d1f_economic_loss_occurs () Bool)
(declare-fun c4c143d1f_guard_accepts_spot () Bool)
(declare-fun c4c143d1f_oracle_used_by_flows () Bool)
(declare-fun c4c143d1f_spot_price_manipulated () Bool)
(assert
 (= c4c143d1f_economic_loss_occurs c4c143d1f_economic_loss_occurs))
(assert
 (= c4c143d1f_guard_accepts_spot c4c143d1f_guard_accepts_spot))
(assert
 (= c4c143d1f_oracle_used_by_flows c4c143d1f_oracle_used_by_flows))
(assert
 (= c4c143d1f_spot_price_manipulated c4c143d1f_spot_price_manipulated))
(define-fun report_preconditions () Bool (and c4c143d1f_spot_price_manipulated c4c143d1f_oracle_used_by_flows))
(define-fun report_safety () Bool (=> (and c4c143d1f_spot_price_manipulated c4c143d1f_oracle_used_by_flows)
    (and (not c4c143d1f_guard_accepts_spot)
         (not c4c143d1f_economic_loss_occurs))))
(define-fun report_effects () Bool (and c4c143d1f_spot_price_manipulated
     c4c143d1f_oracle_used_by_flows
     (not (and (not c4c143d1f_guard_accepts_spot)
               (not c4c143d1f_economic_loss_occurs)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
