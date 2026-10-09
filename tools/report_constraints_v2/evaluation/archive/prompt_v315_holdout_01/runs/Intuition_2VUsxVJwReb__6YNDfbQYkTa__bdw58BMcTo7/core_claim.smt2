; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun valid_period_expired () Bool)
(declare-fun operation_executed_outside_period () Bool)
(assert
 (= valid_period_expired valid_period_expired))
(assert
 (= operation_executed_outside_period operation_executed_outside_period))
(define-fun report_preconditions () Bool (and valid_period_expired valid_period_expired))
(define-fun report_safety () Bool (=> valid_period_expired (not operation_executed_outside_period)))
(define-fun report_effects () Bool (and valid_period_expired operation_executed_outside_period))
