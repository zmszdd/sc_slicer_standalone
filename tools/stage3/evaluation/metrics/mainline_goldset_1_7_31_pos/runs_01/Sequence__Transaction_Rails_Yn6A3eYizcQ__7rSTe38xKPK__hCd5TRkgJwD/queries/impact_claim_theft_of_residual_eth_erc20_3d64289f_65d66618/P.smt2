; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2d6a8177_execute_publicly_callable () Bool)
(declare-fun c2d6a8177_forwarded_value_equals_msg_value () Bool)
(declare-fun c2d6a8177_residual_funds_theft_occurred () Bool)
(declare-fun c2d6a8177_router_residual_funds_nonzero () Bool)
(assert
 (= c2d6a8177_execute_publicly_callable c2d6a8177_execute_publicly_callable))
(assert
 (= c2d6a8177_forwarded_value_equals_msg_value c2d6a8177_forwarded_value_equals_msg_value))
(assert
 (= c2d6a8177_residual_funds_theft_occurred c2d6a8177_residual_funds_theft_occurred))
(assert
 (= c2d6a8177_router_residual_funds_nonzero c2d6a8177_router_residual_funds_nonzero))
(define-fun report_preconditions () Bool (and c2d6a8177_router_residual_funds_nonzero
     c2d6a8177_execute_publicly_callable))
(define-fun report_safety () Bool (=> c2d6a8177_execute_publicly_callable
    c2d6a8177_forwarded_value_equals_msg_value))
(define-fun report_effects () Bool (and c2d6a8177_execute_publicly_callable
     (not c2d6a8177_forwarded_value_equals_msg_value)
     c2d6a8177_residual_funds_theft_occurred))
(assert report_preconditions)
(check-sat)
(get-model)
