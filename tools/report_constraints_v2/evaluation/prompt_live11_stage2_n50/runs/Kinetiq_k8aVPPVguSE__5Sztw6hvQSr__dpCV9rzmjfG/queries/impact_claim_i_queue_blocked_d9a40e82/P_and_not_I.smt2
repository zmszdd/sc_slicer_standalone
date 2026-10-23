; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d5fcfbc_bridge_rejects_tiny () Bool)
(declare-fun c9d5fcfbc_pending_withdrawals_exist () Bool)
(declare-fun c9d5fcfbc_queued_operation_amount () Int)
(declare-fun c9d5fcfbc_stake_amount () Int)
(declare-fun c9d5fcfbc_subsequent_operations_blocked () Bool)
(assert
 (= c9d5fcfbc_bridge_rejects_tiny c9d5fcfbc_bridge_rejects_tiny))
(assert
 (= c9d5fcfbc_pending_withdrawals_exist c9d5fcfbc_pending_withdrawals_exist))
(assert
 (= c9d5fcfbc_queued_operation_amount c9d5fcfbc_queued_operation_amount))
(assert
 (= c9d5fcfbc_stake_amount c9d5fcfbc_stake_amount))
(assert
 (= c9d5fcfbc_subsequent_operations_blocked c9d5fcfbc_subsequent_operations_blocked))
(define-fun report_preconditions () Bool (and (= 10 c9d5fcfbc_stake_amount)
     (= 1 c9d5fcfbc_queued_operation_amount)
     c9d5fcfbc_bridge_rejects_tiny
     c9d5fcfbc_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and (= 10 c9d5fcfbc_stake_amount)
         (= 1 c9d5fcfbc_queued_operation_amount)
         c9d5fcfbc_bridge_rejects_tiny
         c9d5fcfbc_pending_withdrawals_exist)
    (not c9d5fcfbc_subsequent_operations_blocked)))
(define-fun report_effects () Bool (and (= 10 c9d5fcfbc_stake_amount)
     (= 1 c9d5fcfbc_queued_operation_amount)
     c9d5fcfbc_bridge_rejects_tiny
     c9d5fcfbc_pending_withdrawals_exist
     (not (not c9d5fcfbc_subsequent_operations_blocked))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
