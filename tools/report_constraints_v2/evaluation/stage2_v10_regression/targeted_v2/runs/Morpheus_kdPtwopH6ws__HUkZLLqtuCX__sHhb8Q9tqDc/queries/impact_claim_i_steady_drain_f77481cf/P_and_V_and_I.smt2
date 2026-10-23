; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6d96372e_attacker_monitors_mempool () Bool)
(declare-fun c6d96372e_deadline_is_block_timestamp () Bool)
(declare-fun c6d96372e_liquidity_value_expected () Int)
(declare-fun c6d96372e_liquidity_value_received () Int)
(declare-fun c6d96372e_price_validation_present () Bool)
(assert
 (= c6d96372e_attacker_monitors_mempool c6d96372e_attacker_monitors_mempool))
(assert
 (= c6d96372e_deadline_is_block_timestamp c6d96372e_deadline_is_block_timestamp))
(assert
 (= c6d96372e_liquidity_value_expected c6d96372e_liquidity_value_expected))
(assert
 (= c6d96372e_liquidity_value_received c6d96372e_liquidity_value_received))
(assert
 (= c6d96372e_price_validation_present c6d96372e_price_validation_present))
(define-fun report_preconditions () Bool (and c6d96372e_attacker_monitors_mempool
     (not c6d96372e_price_validation_present)
     c6d96372e_deadline_is_block_timestamp))
(define-fun report_safety () Bool (=> (and c6d96372e_attacker_monitors_mempool
         (not c6d96372e_price_validation_present)
         c6d96372e_deadline_is_block_timestamp)
    (>= c6d96372e_liquidity_value_received c6d96372e_liquidity_value_expected)))
(define-fun report_effects () Bool (and c6d96372e_attacker_monitors_mempool
     (not c6d96372e_price_validation_present)
     c6d96372e_deadline_is_block_timestamp
     (not (>= c6d96372e_liquidity_value_received
              c6d96372e_liquidity_value_expected))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
