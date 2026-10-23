; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb98be8fd_bridge_rejects_tiny_op () Bool)
(declare-fun cb98be8fd_pending_withdrawals_deleted () Bool)
(declare-fun cb98be8fd_pending_withdrawals_exist () Bool)
(declare-fun cb98be8fd_stake_amount_gwei () Int)
(declare-fun cb98be8fd_tiny_op_amount () Int)
(declare-fun cb98be8fd_withdrawal_funds_lost () Bool)
(assert
 (= cb98be8fd_bridge_rejects_tiny_op cb98be8fd_bridge_rejects_tiny_op))
(assert
 (= cb98be8fd_pending_withdrawals_deleted cb98be8fd_pending_withdrawals_deleted))
(assert
 (= cb98be8fd_pending_withdrawals_exist cb98be8fd_pending_withdrawals_exist))
(assert
 (= cb98be8fd_stake_amount_gwei cb98be8fd_stake_amount_gwei))
(assert
 (= cb98be8fd_tiny_op_amount cb98be8fd_tiny_op_amount))
(assert
 (= cb98be8fd_withdrawal_funds_lost cb98be8fd_withdrawal_funds_lost))
(define-fun report_preconditions () Bool (and (= 10 cb98be8fd_stake_amount_gwei)
     (= 1 cb98be8fd_tiny_op_amount)
     cb98be8fd_bridge_rejects_tiny_op
     cb98be8fd_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and (= 10 cb98be8fd_stake_amount_gwei)
         (= 1 cb98be8fd_tiny_op_amount)
         cb98be8fd_bridge_rejects_tiny_op
         cb98be8fd_pending_withdrawals_exist)
    (or (not cb98be8fd_pending_withdrawals_deleted)
        (not cb98be8fd_withdrawal_funds_lost))))
(define-fun report_effects () Bool (and (= 10 cb98be8fd_stake_amount_gwei)
     (= 1 cb98be8fd_tiny_op_amount)
     cb98be8fd_bridge_rejects_tiny_op
     cb98be8fd_pending_withdrawals_exist
     (not (or (not cb98be8fd_pending_withdrawals_deleted)
              (not cb98be8fd_withdrawal_funds_lost)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
