; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c83b069b9_attacker_monitors_mempool () Bool)
(declare-fun c83b069b9_deadline_equals_block_timestamp () Bool)
(declare-fun c83b069b9_execution_rate_favorable () Bool)
(declare-fun c83b069b9_price_validated_against_twap () Bool)
(assert
 (= c83b069b9_attacker_monitors_mempool c83b069b9_attacker_monitors_mempool))
(assert
 (= c83b069b9_deadline_equals_block_timestamp c83b069b9_deadline_equals_block_timestamp))
(assert
 (= c83b069b9_execution_rate_favorable c83b069b9_execution_rate_favorable))
(assert
 (= c83b069b9_price_validated_against_twap c83b069b9_price_validated_against_twap))
(define-fun report_preconditions () Bool (and c83b069b9_deadline_equals_block_timestamp
     (not c83b069b9_price_validated_against_twap)
     c83b069b9_attacker_monitors_mempool))
(define-fun report_safety () Bool (=> (and c83b069b9_deadline_equals_block_timestamp
         (not c83b069b9_price_validated_against_twap)
         c83b069b9_attacker_monitors_mempool)
    c83b069b9_execution_rate_favorable))
(define-fun report_effects () Bool (and c83b069b9_deadline_equals_block_timestamp
     (not c83b069b9_price_validated_against_twap)
     c83b069b9_attacker_monitors_mempool
     (not c83b069b9_execution_rate_favorable)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
