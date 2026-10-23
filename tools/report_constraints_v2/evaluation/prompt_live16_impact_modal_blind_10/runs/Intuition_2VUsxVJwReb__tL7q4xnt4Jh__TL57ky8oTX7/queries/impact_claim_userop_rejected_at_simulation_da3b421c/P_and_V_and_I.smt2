; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c648b0dc0_userop_reaches_validation () Bool)
(declare-fun c648b0dc0_userop_rejected_at_simulation_occurs () Bool)
(declare-fun c648b0dc0_wallet_is_claimed () Bool)
(assert
 (= c648b0dc0_userop_reaches_validation c648b0dc0_userop_reaches_validation))
(assert
 (= c648b0dc0_userop_rejected_at_simulation_occurs c648b0dc0_userop_rejected_at_simulation_occurs))
(assert
 (= c648b0dc0_wallet_is_claimed c648b0dc0_wallet_is_claimed))
(define-fun report_preconditions () Bool (and (not c648b0dc0_wallet_is_claimed) c648b0dc0_userop_reaches_validation))
(define-fun report_safety () Bool (=> (and (not c648b0dc0_wallet_is_claimed) c648b0dc0_userop_reaches_validation)
    (not c648b0dc0_userop_rejected_at_simulation_occurs)))
(define-fun report_effects () Bool (and (not c648b0dc0_wallet_is_claimed)
     c648b0dc0_userop_reaches_validation
     (not (not c648b0dc0_userop_rejected_at_simulation_occurs))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
