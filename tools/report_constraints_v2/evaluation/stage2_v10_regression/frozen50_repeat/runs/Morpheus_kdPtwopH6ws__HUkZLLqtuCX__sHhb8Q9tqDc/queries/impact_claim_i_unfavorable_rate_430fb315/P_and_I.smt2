; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca5eb909c_attacker_monitors_mempool () Bool)
(declare-fun ca5eb909c_executes_at_unfavorable_rate () Bool)
(declare-fun ca5eb909c_immediate_execution_no_delay () Bool)
(declare-fun ca5eb909c_price_validation_present () Bool)
(assert
 (= ca5eb909c_attacker_monitors_mempool ca5eb909c_attacker_monitors_mempool))
(assert
 (= ca5eb909c_executes_at_unfavorable_rate ca5eb909c_executes_at_unfavorable_rate))
(assert
 (= ca5eb909c_immediate_execution_no_delay ca5eb909c_immediate_execution_no_delay))
(assert
 (= ca5eb909c_price_validation_present ca5eb909c_price_validation_present))
(define-fun report_preconditions () Bool (and ca5eb909c_attacker_monitors_mempool
     (not ca5eb909c_price_validation_present)
     ca5eb909c_immediate_execution_no_delay))
(define-fun report_safety () Bool (=> (and ca5eb909c_attacker_monitors_mempool
         (not ca5eb909c_price_validation_present)
         ca5eb909c_immediate_execution_no_delay)
    (not ca5eb909c_executes_at_unfavorable_rate)))
(define-fun report_effects () Bool (and ca5eb909c_attacker_monitors_mempool
     (not ca5eb909c_price_validation_present)
     ca5eb909c_immediate_execution_no_delay
     (not (not ca5eb909c_executes_at_unfavorable_rate))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
