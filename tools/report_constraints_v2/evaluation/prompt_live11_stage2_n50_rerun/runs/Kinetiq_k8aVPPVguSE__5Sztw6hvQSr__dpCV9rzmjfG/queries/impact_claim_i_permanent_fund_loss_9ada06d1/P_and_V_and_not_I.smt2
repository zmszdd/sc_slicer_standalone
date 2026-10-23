; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdca60534_bridge_rejects_tiny () Bool)
(declare-fun cdca60534_pending_withdrawals_exist () Bool)
(declare-fun cdca60534_pending_withdrawals_recoverable () Bool)
(declare-fun cdca60534_stake_amount () Int)
(declare-fun cdca60534_tiny_op_amount () Int)
(assert
 (= cdca60534_bridge_rejects_tiny cdca60534_bridge_rejects_tiny))
(assert
 (= cdca60534_pending_withdrawals_exist cdca60534_pending_withdrawals_exist))
(assert
 (= cdca60534_pending_withdrawals_recoverable cdca60534_pending_withdrawals_recoverable))
(assert
 (= cdca60534_stake_amount cdca60534_stake_amount))
(assert
 (= cdca60534_tiny_op_amount cdca60534_tiny_op_amount))
(define-fun report_preconditions () Bool (and (= 10 cdca60534_stake_amount)
     (= 1 cdca60534_tiny_op_amount)
     cdca60534_bridge_rejects_tiny
     cdca60534_pending_withdrawals_exist))
(define-fun report_safety () Bool (=> (and cdca60534_bridge_rejects_tiny cdca60534_pending_withdrawals_exist)
    cdca60534_pending_withdrawals_recoverable))
(define-fun report_effects () Bool (and cdca60534_bridge_rejects_tiny
     cdca60534_pending_withdrawals_exist
     (not cdca60534_pending_withdrawals_recoverable)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
