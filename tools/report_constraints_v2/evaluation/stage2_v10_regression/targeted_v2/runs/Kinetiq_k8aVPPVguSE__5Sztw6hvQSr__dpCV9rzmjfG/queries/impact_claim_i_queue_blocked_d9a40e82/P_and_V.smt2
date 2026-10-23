; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d5fcfbc_bridge_rejects_tiny_op () Bool)
(declare-fun c9d5fcfbc_pending_withdrawals_exist () Bool)
(declare-fun c9d5fcfbc_stake_amount_gwei () Int)
(declare-fun c9d5fcfbc_subsequent_ops_blocked () Bool)
(declare-fun c9d5fcfbc_tiny_op_amount () Int)
(assert
 (= c9d5fcfbc_bridge_rejects_tiny_op c9d5fcfbc_bridge_rejects_tiny_op))
(assert
 (= c9d5fcfbc_pending_withdrawals_exist c9d5fcfbc_pending_withdrawals_exist))
(assert
 (= c9d5fcfbc_stake_amount_gwei c9d5fcfbc_stake_amount_gwei))
(assert
 (= c9d5fcfbc_subsequent_ops_blocked c9d5fcfbc_subsequent_ops_blocked))
(assert
 (= c9d5fcfbc_tiny_op_amount c9d5fcfbc_tiny_op_amount))
(define-fun report_preconditions () Bool (and (= 10 c9d5fcfbc_stake_amount_gwei)
     (= 1 c9d5fcfbc_tiny_op_amount)
     c9d5fcfbc_bridge_rejects_tiny_op
     c9d5fcfbc_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and (= 10 c9d5fcfbc_stake_amount_gwei)
         (= 1 c9d5fcfbc_tiny_op_amount)
         c9d5fcfbc_bridge_rejects_tiny_op
         c9d5fcfbc_pending_withdrawals_exist)
    (not c9d5fcfbc_subsequent_ops_blocked)))
(define-fun report_effects () Bool (and (= 10 c9d5fcfbc_stake_amount_gwei)
     (= 1 c9d5fcfbc_tiny_op_amount)
     c9d5fcfbc_bridge_rejects_tiny_op
     c9d5fcfbc_pending_withdrawals_exist
     (not (not c9d5fcfbc_subsequent_ops_blocked))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
