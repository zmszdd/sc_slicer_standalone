; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2142827b_admin_forced_to_reset_or_block () Bool)
(declare-fun c2142827b_bridge_rejects_tiny_amount () Bool)
(declare-fun c2142827b_pending_withdrawal_requests_exist () Bool)
(declare-fun c2142827b_queue_permanently_blocked () Bool)
(declare-fun c2142827b_stake_amount_gwei () Int)
(declare-fun c2142827b_tiny_l1_operation_amount () Int)
(assert
 (= c2142827b_admin_forced_to_reset_or_block c2142827b_admin_forced_to_reset_or_block))
(assert
 (= c2142827b_bridge_rejects_tiny_amount c2142827b_bridge_rejects_tiny_amount))
(assert
 (= c2142827b_pending_withdrawal_requests_exist c2142827b_pending_withdrawal_requests_exist))
(assert
 (= c2142827b_queue_permanently_blocked c2142827b_queue_permanently_blocked))
(assert
 (= c2142827b_stake_amount_gwei c2142827b_stake_amount_gwei))
(assert
 (= c2142827b_tiny_l1_operation_amount c2142827b_tiny_l1_operation_amount))
(define-fun report_preconditions () Bool (and (= 10 c2142827b_stake_amount_gwei)
     (= 1 c2142827b_tiny_l1_operation_amount)
     c2142827b_pending_withdrawal_requests_exist
     c2142827b_bridge_rejects_tiny_amount))
(define-fun report_safety () Bool (=> (and (= 10 c2142827b_stake_amount_gwei)
         (= 1 c2142827b_tiny_l1_operation_amount)
         c2142827b_pending_withdrawal_requests_exist
         c2142827b_bridge_rejects_tiny_amount)
    (and (not c2142827b_queue_permanently_blocked)
         (not c2142827b_admin_forced_to_reset_or_block))))
(define-fun report_effects () Bool (and (= 10 c2142827b_stake_amount_gwei)
     (= 1 c2142827b_tiny_l1_operation_amount)
     c2142827b_pending_withdrawal_requests_exist
     c2142827b_bridge_rejects_tiny_amount
     (not (and (not c2142827b_queue_permanently_blocked)
               (not c2142827b_admin_forced_to_reset_or_block)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
