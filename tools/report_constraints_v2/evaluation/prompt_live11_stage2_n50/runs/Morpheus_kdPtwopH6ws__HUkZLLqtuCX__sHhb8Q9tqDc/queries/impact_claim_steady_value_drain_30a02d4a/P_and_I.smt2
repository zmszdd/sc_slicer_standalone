; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2bc1a36d_attacker_observes_pending_addition () Bool)
(declare-fun c2bc1a36d_deadline_equals_block_timestamp () Bool)
(declare-fun c2bc1a36d_liquidity_value_owed () Int)
(declare-fun c2bc1a36d_liquidity_value_received () Int)
(declare-fun c2bc1a36d_price_validated_against_twap () Bool)
(assert
 (= c2bc1a36d_attacker_observes_pending_addition c2bc1a36d_attacker_observes_pending_addition))
(assert
 (= c2bc1a36d_deadline_equals_block_timestamp c2bc1a36d_deadline_equals_block_timestamp))
(assert
 (= c2bc1a36d_liquidity_value_owed c2bc1a36d_liquidity_value_owed))
(assert
 (= c2bc1a36d_liquidity_value_received c2bc1a36d_liquidity_value_received))
(assert
 (= c2bc1a36d_price_validated_against_twap c2bc1a36d_price_validated_against_twap))
(define-fun report_preconditions () Bool (and c2bc1a36d_deadline_equals_block_timestamp
     (not c2bc1a36d_price_validated_against_twap)
     c2bc1a36d_attacker_observes_pending_addition))
(define-fun report_safety () Bool (=> (and c2bc1a36d_deadline_equals_block_timestamp
         (not c2bc1a36d_price_validated_against_twap)
         c2bc1a36d_attacker_observes_pending_addition)
    (>= c2bc1a36d_liquidity_value_received c2bc1a36d_liquidity_value_owed)))
(define-fun report_effects () Bool (and c2bc1a36d_deadline_equals_block_timestamp
     (not c2bc1a36d_price_validated_against_twap)
     c2bc1a36d_attacker_observes_pending_addition
     (not (>= c2bc1a36d_liquidity_value_received c2bc1a36d_liquidity_value_owed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
