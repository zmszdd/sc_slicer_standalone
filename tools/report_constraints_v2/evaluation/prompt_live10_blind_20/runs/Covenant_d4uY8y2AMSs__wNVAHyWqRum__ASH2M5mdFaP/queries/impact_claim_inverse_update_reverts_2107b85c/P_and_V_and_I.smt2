; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4cedc7ec_adapter_chain_configured () Bool)
(declare-fun c4cedc7ec_inverse_direction_call () Bool)
(declare-fun c4cedc7ec_update_reverted () Bool)
(assert
 (= c4cedc7ec_adapter_chain_configured c4cedc7ec_adapter_chain_configured))
(assert
 (= c4cedc7ec_inverse_direction_call c4cedc7ec_inverse_direction_call))
(assert
 (= c4cedc7ec_update_reverted c4cedc7ec_update_reverted))
(define-fun report_preconditions () Bool (and c4cedc7ec_inverse_direction_call c4cedc7ec_adapter_chain_configured))
(define-fun report_safety () Bool (=> (and c4cedc7ec_inverse_direction_call c4cedc7ec_adapter_chain_configured)
    (not c4cedc7ec_update_reverted)))
(define-fun report_effects () Bool (and c4cedc7ec_inverse_direction_call
     c4cedc7ec_adapter_chain_configured
     (not (not c4cedc7ec_update_reverted))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
