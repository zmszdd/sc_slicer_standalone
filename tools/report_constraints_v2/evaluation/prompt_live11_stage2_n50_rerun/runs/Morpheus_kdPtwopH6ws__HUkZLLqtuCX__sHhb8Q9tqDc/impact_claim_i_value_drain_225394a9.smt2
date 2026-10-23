; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8cfd5daf_attacker_monitors_mempool () Bool)
(declare-fun c8cfd5daf_deadline_is_block_timestamp () Bool)
(declare-fun c8cfd5daf_liquidity_value_commensurate () Bool)
(declare-fun c8cfd5daf_price_validation_present () Bool)
(declare-fun c8cfd5daf_strategy_value_drained () Bool)
(assert
 (= c8cfd5daf_attacker_monitors_mempool c8cfd5daf_attacker_monitors_mempool))
(assert
 (= c8cfd5daf_deadline_is_block_timestamp c8cfd5daf_deadline_is_block_timestamp))
(assert
 (= c8cfd5daf_liquidity_value_commensurate c8cfd5daf_liquidity_value_commensurate))
(assert
 (= c8cfd5daf_price_validation_present c8cfd5daf_price_validation_present))
(assert
 (= c8cfd5daf_strategy_value_drained c8cfd5daf_strategy_value_drained))
(define-fun report_preconditions () Bool (and c8cfd5daf_attacker_monitors_mempool
     (not c8cfd5daf_price_validation_present)
     c8cfd5daf_deadline_is_block_timestamp))
(define-fun report_safety () Bool (=> c8cfd5daf_attacker_monitors_mempool
    (and c8cfd5daf_liquidity_value_commensurate
         (not c8cfd5daf_strategy_value_drained))))
(define-fun report_effects () Bool (and c8cfd5daf_attacker_monitors_mempool
     (not (and c8cfd5daf_liquidity_value_commensurate
               (not c8cfd5daf_strategy_value_drained)))))
