; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdd97e44d_bridge_rejects_tiny () Bool)
(declare-fun cdd97e44d_khype_burned_on_queue () Bool)
(declare-fun cdd97e44d_pending_funds_lost () Bool)
(declare-fun cdd97e44d_pending_withdrawals_exist () Bool)
(declare-fun cdd97e44d_staked_amount_gwei () Int)
(declare-fun cdd97e44d_subsequent_ops_blocked () Bool)
(declare-fun cdd97e44d_tiny_l1_op_amount () Int)
(assert
 (= cdd97e44d_bridge_rejects_tiny cdd97e44d_bridge_rejects_tiny))
(assert
 (= cdd97e44d_khype_burned_on_queue cdd97e44d_khype_burned_on_queue))
(assert
 (= cdd97e44d_pending_funds_lost cdd97e44d_pending_funds_lost))
(assert
 (= cdd97e44d_pending_withdrawals_exist cdd97e44d_pending_withdrawals_exist))
(assert
 (= cdd97e44d_staked_amount_gwei cdd97e44d_staked_amount_gwei))
(assert
 (= cdd97e44d_subsequent_ops_blocked cdd97e44d_subsequent_ops_blocked))
(assert
 (= cdd97e44d_tiny_l1_op_amount cdd97e44d_tiny_l1_op_amount))
(define-fun report_preconditions () Bool (and (= 10 cdd97e44d_staked_amount_gwei)
     (= 1 cdd97e44d_tiny_l1_op_amount)
     cdd97e44d_khype_burned_on_queue
     cdd97e44d_bridge_rejects_tiny
     cdd97e44d_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and cdd97e44d_pending_withdrawals_exist cdd97e44d_bridge_rejects_tiny)
    (or (not cdd97e44d_subsequent_ops_blocked)
        (not cdd97e44d_pending_funds_lost))))
(define-fun report_effects () Bool (and cdd97e44d_pending_withdrawals_exist
     cdd97e44d_bridge_rejects_tiny
     (not (or (not cdd97e44d_subsequent_ops_blocked)
              (not cdd97e44d_pending_funds_lost)))))
