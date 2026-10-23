; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5af9b2b7_attacker_monitors_mempool_occurred () Bool)
(declare-fun c5af9b2b7_execution_rate_manipulable () Bool)
(declare-fun c5af9b2b7_liquidity_addition_pending_occurred () Bool)
(assert
 (= c5af9b2b7_attacker_monitors_mempool_occurred c5af9b2b7_attacker_monitors_mempool_occurred))
(assert
 (= c5af9b2b7_execution_rate_manipulable c5af9b2b7_execution_rate_manipulable))
(assert
 (= c5af9b2b7_liquidity_addition_pending_occurred c5af9b2b7_liquidity_addition_pending_occurred))
(define-fun report_preconditions () Bool (and c5af9b2b7_attacker_monitors_mempool_occurred
     c5af9b2b7_liquidity_addition_pending_occurred))
(define-fun report_safety () Bool (=> (and c5af9b2b7_attacker_monitors_mempool_occurred
         c5af9b2b7_liquidity_addition_pending_occurred)
    (not c5af9b2b7_execution_rate_manipulable)))
(define-fun report_effects () Bool (and c5af9b2b7_attacker_monitors_mempool_occurred
     c5af9b2b7_liquidity_addition_pending_occurred
     (not (not c5af9b2b7_execution_rate_manipulable))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
