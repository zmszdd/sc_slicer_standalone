; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1e9c2ebf_admin_forced_dilemma () Bool)
(declare-fun c1e9c2ebf_bridge_rejects_tiny () Bool)
(declare-fun c1e9c2ebf_min_stake_amount () Int)
(declare-fun c1e9c2ebf_pending_withdrawals_exist () Bool)
(declare-fun c1e9c2ebf_subsequent_ops_blocked () Bool)
(declare-fun c1e9c2ebf_tiny_op_amount () Int)
(assert
 (= c1e9c2ebf_admin_forced_dilemma c1e9c2ebf_admin_forced_dilemma))
(assert
 (= c1e9c2ebf_bridge_rejects_tiny c1e9c2ebf_bridge_rejects_tiny))
(assert
 (= c1e9c2ebf_min_stake_amount c1e9c2ebf_min_stake_amount))
(assert
 (= c1e9c2ebf_pending_withdrawals_exist c1e9c2ebf_pending_withdrawals_exist))
(assert
 (= c1e9c2ebf_subsequent_ops_blocked c1e9c2ebf_subsequent_ops_blocked))
(assert
 (= c1e9c2ebf_tiny_op_amount c1e9c2ebf_tiny_op_amount))
(define-fun report_preconditions () Bool (and (= 10 c1e9c2ebf_min_stake_amount)
     (= 1 c1e9c2ebf_tiny_op_amount)
     c1e9c2ebf_bridge_rejects_tiny
     c1e9c2ebf_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and (= 10 c1e9c2ebf_min_stake_amount)
         (= 1 c1e9c2ebf_tiny_op_amount)
         c1e9c2ebf_bridge_rejects_tiny
         c1e9c2ebf_pending_withdrawals_exist)
    (and (not c1e9c2ebf_subsequent_ops_blocked)
         (not c1e9c2ebf_admin_forced_dilemma))))
(define-fun report_effects () Bool (and (= 10 c1e9c2ebf_min_stake_amount)
     (= 1 c1e9c2ebf_tiny_op_amount)
     c1e9c2ebf_bridge_rejects_tiny
     c1e9c2ebf_pending_withdrawals_exist
     (not (and (not c1e9c2ebf_subsequent_ops_blocked)
               (not c1e9c2ebf_admin_forced_dilemma)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
