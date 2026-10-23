; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2b9b53cf_attacker_monitors_mempool () Bool)
(declare-fun c2b9b53cf_deadline_equals_block_timestamp () Bool)
(declare-fun c2b9b53cf_liquidity_value_expected () Int)
(declare-fun c2b9b53cf_liquidity_value_received () Int)
(declare-fun c2b9b53cf_price_validated_against_twap () Bool)
(assert
 (= c2b9b53cf_attacker_monitors_mempool c2b9b53cf_attacker_monitors_mempool))
(assert
 (= c2b9b53cf_deadline_equals_block_timestamp c2b9b53cf_deadline_equals_block_timestamp))
(assert
 (= c2b9b53cf_liquidity_value_expected c2b9b53cf_liquidity_value_expected))
(assert
 (= c2b9b53cf_liquidity_value_received c2b9b53cf_liquidity_value_received))
(assert
 (= c2b9b53cf_price_validated_against_twap c2b9b53cf_price_validated_against_twap))
(define-fun report_preconditions () Bool (and c2b9b53cf_deadline_equals_block_timestamp
     (not c2b9b53cf_price_validated_against_twap)
     c2b9b53cf_attacker_monitors_mempool))
(define-fun report_safety () Bool (=> (and c2b9b53cf_deadline_equals_block_timestamp
         (not c2b9b53cf_price_validated_against_twap)
         c2b9b53cf_attacker_monitors_mempool)
    (>= c2b9b53cf_liquidity_value_received c2b9b53cf_liquidity_value_expected)))
(define-fun report_effects () Bool (and c2b9b53cf_deadline_equals_block_timestamp
     (not c2b9b53cf_price_validated_against_twap)
     c2b9b53cf_attacker_monitors_mempool
     (not (>= c2b9b53cf_liquidity_value_received
              c2b9b53cf_liquidity_value_expected))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
