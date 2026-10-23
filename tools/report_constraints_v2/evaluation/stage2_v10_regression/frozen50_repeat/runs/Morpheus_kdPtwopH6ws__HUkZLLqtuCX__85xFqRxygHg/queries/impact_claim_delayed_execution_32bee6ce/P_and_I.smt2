; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c68a74471_executed_after_deadline () Bool)
(declare-fun c68a74471_tx_pending () Bool)
(assert
 (= c68a74471_executed_after_deadline c68a74471_executed_after_deadline))
(assert
 (= c68a74471_tx_pending c68a74471_tx_pending))
(define-fun report_preconditions () Bool c68a74471_tx_pending)
(define-fun report_safety () Bool (=> c68a74471_tx_pending (not c68a74471_executed_after_deadline)))
(define-fun report_effects () Bool (and c68a74471_tx_pending (not (not c68a74471_executed_after_deadline))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
