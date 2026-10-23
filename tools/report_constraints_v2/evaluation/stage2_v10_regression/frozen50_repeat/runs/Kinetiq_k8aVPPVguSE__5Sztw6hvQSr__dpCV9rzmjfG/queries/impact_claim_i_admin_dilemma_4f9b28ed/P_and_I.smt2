; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1e9c2ebf_bridge_rejects_tiny_op () Bool)
(declare-fun c1e9c2ebf_pending_withdrawals_exist () Bool)
(declare-fun c1e9c2ebf_queue_permanently_blocked () Bool)
(declare-fun c1e9c2ebf_reset_loses_user_funds () Bool)
(declare-fun c1e9c2ebf_stake_amount () Int)
(declare-fun c1e9c2ebf_tiny_op_amount () Int)
(assert
 (= c1e9c2ebf_bridge_rejects_tiny_op c1e9c2ebf_bridge_rejects_tiny_op))
(assert
 (= c1e9c2ebf_pending_withdrawals_exist c1e9c2ebf_pending_withdrawals_exist))
(assert
 (= c1e9c2ebf_queue_permanently_blocked c1e9c2ebf_queue_permanently_blocked))
(assert
 (= c1e9c2ebf_reset_loses_user_funds c1e9c2ebf_reset_loses_user_funds))
(assert
 (= c1e9c2ebf_stake_amount c1e9c2ebf_stake_amount))
(assert
 (= c1e9c2ebf_tiny_op_amount c1e9c2ebf_tiny_op_amount))
(define-fun report_preconditions () Bool (and (= 10 c1e9c2ebf_stake_amount)
     (= 1 c1e9c2ebf_tiny_op_amount)
     c1e9c2ebf_bridge_rejects_tiny_op
     c1e9c2ebf_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and c1e9c2ebf_bridge_rejects_tiny_op c1e9c2ebf_pending_withdrawals_exist)
    (and (not c1e9c2ebf_queue_permanently_blocked)
         (not c1e9c2ebf_reset_loses_user_funds))))
(define-fun report_effects () Bool (and c1e9c2ebf_bridge_rejects_tiny_op
     c1e9c2ebf_pending_withdrawals_exist
     (not (and (not c1e9c2ebf_queue_permanently_blocked)
               (not c1e9c2ebf_reset_loses_user_funds)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
