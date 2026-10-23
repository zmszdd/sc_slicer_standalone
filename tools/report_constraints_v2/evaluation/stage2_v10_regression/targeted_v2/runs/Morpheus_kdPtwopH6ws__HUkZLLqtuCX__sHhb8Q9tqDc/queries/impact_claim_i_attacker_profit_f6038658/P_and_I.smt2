; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3c1ca5f9_attacker_monitors_mempool () Bool)
(declare-fun c3c1ca5f9_attacker_profit_captured () Bool)
(declare-fun c3c1ca5f9_deadline_is_block_timestamp () Bool)
(declare-fun c3c1ca5f9_liquidity_value_matches_assets () Bool)
(declare-fun c3c1ca5f9_price_validation_present () Bool)
(assert
 (= c3c1ca5f9_attacker_monitors_mempool c3c1ca5f9_attacker_monitors_mempool))
(assert
 (= c3c1ca5f9_attacker_profit_captured c3c1ca5f9_attacker_profit_captured))
(assert
 (= c3c1ca5f9_deadline_is_block_timestamp c3c1ca5f9_deadline_is_block_timestamp))
(assert
 (= c3c1ca5f9_liquidity_value_matches_assets c3c1ca5f9_liquidity_value_matches_assets))
(assert
 (= c3c1ca5f9_price_validation_present c3c1ca5f9_price_validation_present))
(define-fun report_preconditions () Bool (and c3c1ca5f9_attacker_monitors_mempool
     (not c3c1ca5f9_price_validation_present)
     c3c1ca5f9_deadline_is_block_timestamp))
(define-fun report_safety () Bool (=> (and c3c1ca5f9_attacker_monitors_mempool
         (not c3c1ca5f9_price_validation_present)
         c3c1ca5f9_deadline_is_block_timestamp)
    (and c3c1ca5f9_liquidity_value_matches_assets
         (not c3c1ca5f9_attacker_profit_captured))))
(define-fun report_effects () Bool (and c3c1ca5f9_attacker_monitors_mempool
     (not c3c1ca5f9_price_validation_present)
     c3c1ca5f9_deadline_is_block_timestamp
     (not (and c3c1ca5f9_liquidity_value_matches_assets
               (not c3c1ca5f9_attacker_profit_captured)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
