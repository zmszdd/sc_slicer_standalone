; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc22d83ee_attacker_monitors_mempool () Bool)
(declare-fun cc22d83ee_deadline_is_block_timestamp () Bool)
(declare-fun cc22d83ee_liquidity_value_owed () Int)
(declare-fun cc22d83ee_liquidity_value_received () Int)
(declare-fun cc22d83ee_price_validation_present () Bool)
(assert
 (= cc22d83ee_attacker_monitors_mempool cc22d83ee_attacker_monitors_mempool))
(assert
 (= cc22d83ee_deadline_is_block_timestamp cc22d83ee_deadline_is_block_timestamp))
(assert
 (= cc22d83ee_liquidity_value_owed cc22d83ee_liquidity_value_owed))
(assert
 (= cc22d83ee_liquidity_value_received cc22d83ee_liquidity_value_received))
(assert
 (= cc22d83ee_price_validation_present cc22d83ee_price_validation_present))
(define-fun report_preconditions () Bool (and cc22d83ee_attacker_monitors_mempool
     (not cc22d83ee_price_validation_present)
     cc22d83ee_deadline_is_block_timestamp))
(define-fun report_safety () Bool (=> (and cc22d83ee_attacker_monitors_mempool
         (not cc22d83ee_price_validation_present)
         cc22d83ee_deadline_is_block_timestamp)
    (>= cc22d83ee_liquidity_value_received cc22d83ee_liquidity_value_owed)))
(define-fun report_effects () Bool (and cc22d83ee_attacker_monitors_mempool
     (not cc22d83ee_price_validation_present)
     cc22d83ee_deadline_is_block_timestamp
     (not (>= cc22d83ee_liquidity_value_received cc22d83ee_liquidity_value_owed))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
