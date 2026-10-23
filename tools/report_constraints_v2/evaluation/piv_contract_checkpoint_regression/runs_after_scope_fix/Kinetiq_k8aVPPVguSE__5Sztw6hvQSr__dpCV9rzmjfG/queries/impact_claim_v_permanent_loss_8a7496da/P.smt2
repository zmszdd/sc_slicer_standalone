; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c55e1dbfc_bridge_rejects_tiny_op () Bool)
(declare-fun c55e1dbfc_pending_funds_lost_permanently () Bool)
(declare-fun c55e1dbfc_pending_withdrawal_requests_exist () Bool)
(declare-fun c55e1dbfc_queue_reset_occurred () Bool)
(declare-fun c55e1dbfc_stake_amount_gwei () Int)
(declare-fun c55e1dbfc_tiny_l1_op_amount () Int)
(assert
 (= c55e1dbfc_bridge_rejects_tiny_op c55e1dbfc_bridge_rejects_tiny_op))
(assert
 (= c55e1dbfc_pending_funds_lost_permanently c55e1dbfc_pending_funds_lost_permanently))
(assert
 (= c55e1dbfc_pending_withdrawal_requests_exist c55e1dbfc_pending_withdrawal_requests_exist))
(assert
 (= c55e1dbfc_queue_reset_occurred c55e1dbfc_queue_reset_occurred))
(assert
 (= c55e1dbfc_stake_amount_gwei c55e1dbfc_stake_amount_gwei))
(assert
 (= c55e1dbfc_tiny_l1_op_amount c55e1dbfc_tiny_l1_op_amount))
(define-fun report_preconditions () Bool (and (= 10 c55e1dbfc_stake_amount_gwei)
     (= 1 c55e1dbfc_tiny_l1_op_amount)
     c55e1dbfc_pending_withdrawal_requests_exist
     c55e1dbfc_bridge_rejects_tiny_op))
(define-fun report_safety () Bool (=> (and c55e1dbfc_pending_withdrawal_requests_exist
         c55e1dbfc_queue_reset_occurred)
    (not c55e1dbfc_pending_funds_lost_permanently)))
(define-fun report_effects () Bool (and c55e1dbfc_pending_withdrawal_requests_exist
     c55e1dbfc_queue_reset_occurred
     (not (not c55e1dbfc_pending_funds_lost_permanently))))
(assert report_preconditions)
(check-sat)
(get-model)
