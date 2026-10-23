; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c70d323c2_backstop_liquidation_occurs () Bool)
(declare-fun c70d323c2_backstop_liquidation_scope () Bool)
(declare-fun c70d323c2_backstop_rewards_paid () Bool)
(declare-fun c70d323c2_position_has_positive_upnl () Bool)
(assert
 (= c70d323c2_backstop_liquidation_occurs c70d323c2_backstop_liquidation_occurs))
(assert
 (= c70d323c2_backstop_liquidation_scope c70d323c2_backstop_liquidation_scope))
(assert
 (= c70d323c2_backstop_rewards_paid c70d323c2_backstop_rewards_paid))
(assert
 (= c70d323c2_position_has_positive_upnl c70d323c2_position_has_positive_upnl))
(define-fun report_preconditions () Bool c70d323c2_position_has_positive_upnl)
(define-fun report_safety () Bool (=> (and c70d323c2_backstop_liquidation_occurs
         c70d323c2_backstop_liquidation_scope)
    (=> (and c70d323c2_backstop_liquidation_occurs
             c70d323c2_backstop_liquidation_scope)
        c70d323c2_backstop_rewards_paid)))
(define-fun report_effects () Bool (and (and c70d323c2_backstop_liquidation_occurs
          c70d323c2_backstop_liquidation_scope)
     (and c70d323c2_backstop_liquidation_occurs
          c70d323c2_backstop_liquidation_scope)
     (not c70d323c2_backstop_rewards_paid)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
