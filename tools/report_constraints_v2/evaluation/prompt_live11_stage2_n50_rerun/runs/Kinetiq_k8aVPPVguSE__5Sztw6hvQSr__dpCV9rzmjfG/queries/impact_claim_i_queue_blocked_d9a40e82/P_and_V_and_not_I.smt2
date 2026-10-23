; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d5fcfbc_bridge_rejects_tiny () Bool)
(declare-fun c9d5fcfbc_min_stake_amount () Int)
(declare-fun c9d5fcfbc_pending_withdrawals_exist () Bool)
(declare-fun c9d5fcfbc_subsequent_ops_blocked () Bool)
(declare-fun c9d5fcfbc_tiny_op_queued () Bool)
(assert
 (= c9d5fcfbc_bridge_rejects_tiny c9d5fcfbc_bridge_rejects_tiny))
(assert
 (= c9d5fcfbc_min_stake_amount c9d5fcfbc_min_stake_amount))
(assert
 (= c9d5fcfbc_pending_withdrawals_exist c9d5fcfbc_pending_withdrawals_exist))
(assert
 (= c9d5fcfbc_subsequent_ops_blocked c9d5fcfbc_subsequent_ops_blocked))
(assert
 (= c9d5fcfbc_tiny_op_queued c9d5fcfbc_tiny_op_queued))
(define-fun report_preconditions () Bool (and (= 10 c9d5fcfbc_min_stake_amount)
     c9d5fcfbc_tiny_op_queued
     c9d5fcfbc_bridge_rejects_tiny
     c9d5fcfbc_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and (= 10 c9d5fcfbc_min_stake_amount)
         c9d5fcfbc_tiny_op_queued
         c9d5fcfbc_bridge_rejects_tiny
         c9d5fcfbc_pending_withdrawals_exist)
    (not c9d5fcfbc_subsequent_ops_blocked)))
(define-fun report_effects () Bool (and (= 10 c9d5fcfbc_min_stake_amount)
     c9d5fcfbc_tiny_op_queued
     c9d5fcfbc_bridge_rejects_tiny
     c9d5fcfbc_pending_withdrawals_exist
     (not (not c9d5fcfbc_subsequent_ops_blocked))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
