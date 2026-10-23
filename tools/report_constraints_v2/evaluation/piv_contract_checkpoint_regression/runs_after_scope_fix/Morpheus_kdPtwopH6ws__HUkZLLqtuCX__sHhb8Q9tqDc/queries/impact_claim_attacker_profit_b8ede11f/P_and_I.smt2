; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce56c9738_attacker_monitors_mempool_occurred () Bool)
(declare-fun ce56c9738_attacker_profit_captured () Bool)
(declare-fun ce56c9738_liquidity_addition_pending () Bool)
(declare-fun ce56c9738_protocol_received_fair_liquidity_value () Bool)
(assert
 (= ce56c9738_attacker_monitors_mempool_occurred ce56c9738_attacker_monitors_mempool_occurred))
(assert
 (= ce56c9738_attacker_profit_captured ce56c9738_attacker_profit_captured))
(assert
 (= ce56c9738_liquidity_addition_pending ce56c9738_liquidity_addition_pending))
(assert
 (= ce56c9738_protocol_received_fair_liquidity_value ce56c9738_protocol_received_fair_liquidity_value))
(define-fun report_preconditions () Bool (and ce56c9738_attacker_monitors_mempool_occurred
     ce56c9738_liquidity_addition_pending))
(define-fun report_safety () Bool (=> (and ce56c9738_attacker_monitors_mempool_occurred
         ce56c9738_liquidity_addition_pending)
    (and ce56c9738_protocol_received_fair_liquidity_value
         (not ce56c9738_attacker_profit_captured))))
(define-fun report_effects () Bool (and ce56c9738_attacker_monitors_mempool_occurred
     ce56c9738_liquidity_addition_pending
     (not (and ce56c9738_protocol_received_fair_liquidity_value
               (not ce56c9738_attacker_profit_captured)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
