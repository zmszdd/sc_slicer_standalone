; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c04d3abb7_bridge_rejects_tiny_amount () Bool)
(declare-fun c04d3abb7_pending_withdrawal_requests_exist () Bool)
(declare-fun c04d3abb7_stake_amount_gwei () Int)
(declare-fun c04d3abb7_subsequent_operations_blocked () Bool)
(declare-fun c04d3abb7_tiny_l1_operation_amount () Int)
(assert
 (= c04d3abb7_bridge_rejects_tiny_amount c04d3abb7_bridge_rejects_tiny_amount))
(assert
 (= c04d3abb7_pending_withdrawal_requests_exist c04d3abb7_pending_withdrawal_requests_exist))
(assert
 (= c04d3abb7_stake_amount_gwei c04d3abb7_stake_amount_gwei))
(assert
 (= c04d3abb7_subsequent_operations_blocked c04d3abb7_subsequent_operations_blocked))
(assert
 (= c04d3abb7_tiny_l1_operation_amount c04d3abb7_tiny_l1_operation_amount))
(define-fun report_preconditions () Bool (and (= 10 c04d3abb7_stake_amount_gwei)
     (= 1 c04d3abb7_tiny_l1_operation_amount)
     c04d3abb7_pending_withdrawal_requests_exist
     c04d3abb7_bridge_rejects_tiny_amount))
(define-fun report_safety () Bool (=> (and (= 10 c04d3abb7_stake_amount_gwei)
         (= 1 c04d3abb7_tiny_l1_operation_amount)
         c04d3abb7_pending_withdrawal_requests_exist
         c04d3abb7_bridge_rejects_tiny_amount)
    (not c04d3abb7_subsequent_operations_blocked)))
(define-fun report_effects () Bool (and (= 10 c04d3abb7_stake_amount_gwei)
     (= 1 c04d3abb7_tiny_l1_operation_amount)
     c04d3abb7_pending_withdrawal_requests_exist
     c04d3abb7_bridge_rejects_tiny_amount
     (not (not c04d3abb7_subsequent_operations_blocked))))
