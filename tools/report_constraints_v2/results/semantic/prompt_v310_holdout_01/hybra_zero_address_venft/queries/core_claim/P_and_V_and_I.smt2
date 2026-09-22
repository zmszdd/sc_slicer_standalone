; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun locked_value_venft () Bool)
(declare-fun transfer_to_zero () Bool)
(declare-fun caller_authorized () Bool)
(declare-fun no_upstream_zero_check () Bool)
(declare-fun ownership_zero () Bool)
(assert
 (= locked_value_venft locked_value_venft))
(assert
 (= transfer_to_zero transfer_to_zero))
(assert
 (= caller_authorized caller_authorized))
(assert
 (= no_upstream_zero_check no_upstream_zero_check))
(assert
 (= ownership_zero ownership_zero))
(define-fun report_preconditions () Bool (and locked_value_venft
     transfer_to_zero
     caller_authorized
     no_upstream_zero_check))
(define-fun report_safety () Bool (=> transfer_to_zero (not ownership_zero)))
(define-fun report_effects () Bool (and transfer_to_zero ownership_zero))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
