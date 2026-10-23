; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca5eb909c_attacker_monitors_mempool () Bool)
(declare-fun ca5eb909c_deadline_is_block_timestamp () Bool)
(declare-fun ca5eb909c_execution_rate_favorable () Bool)
(declare-fun ca5eb909c_price_validation_present () Bool)
(assert
 (= ca5eb909c_attacker_monitors_mempool ca5eb909c_attacker_monitors_mempool))
(assert
 (= ca5eb909c_deadline_is_block_timestamp ca5eb909c_deadline_is_block_timestamp))
(assert
 (= ca5eb909c_execution_rate_favorable ca5eb909c_execution_rate_favorable))
(assert
 (= ca5eb909c_price_validation_present ca5eb909c_price_validation_present))
(define-fun report_preconditions () Bool (and ca5eb909c_attacker_monitors_mempool
     (not ca5eb909c_price_validation_present)
     ca5eb909c_deadline_is_block_timestamp))
(define-fun report_safety () Bool (=> (and ca5eb909c_attacker_monitors_mempool
         (not ca5eb909c_price_validation_present)
         ca5eb909c_deadline_is_block_timestamp)
    ca5eb909c_execution_rate_favorable))
(define-fun report_effects () Bool (and ca5eb909c_attacker_monitors_mempool
     (not ca5eb909c_price_validation_present)
     ca5eb909c_deadline_is_block_timestamp
     (not ca5eb909c_execution_rate_favorable)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
