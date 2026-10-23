; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44f49f8a_l1_command_1_executed () Bool)
(declare-fun c44f49f8a_l1_command_1_queued () Bool)
(declare-fun c44f49f8a_l1_command_1_still_queued_after_cancel () Bool)
(declare-fun c44f49f8a_l2_l1_desynced () Bool)
(declare-fun c44f49f8a_l2_withdrawal_cancelled () Bool)
(declare-fun c44f49f8a_staked_eth () Int)
(assert
 (= c44f49f8a_l1_command_1_executed c44f49f8a_l1_command_1_executed))
(assert
 (= c44f49f8a_l1_command_1_queued c44f49f8a_l1_command_1_queued))
(assert
 (= c44f49f8a_l1_command_1_still_queued_after_cancel c44f49f8a_l1_command_1_still_queued_after_cancel))
(assert
 (= c44f49f8a_l2_l1_desynced c44f49f8a_l2_l1_desynced))
(assert
 (= c44f49f8a_l2_withdrawal_cancelled c44f49f8a_l2_withdrawal_cancelled))
(assert
 (= c44f49f8a_staked_eth c44f49f8a_staked_eth))
(define-fun report_preconditions () Bool (and (= 1 c44f49f8a_staked_eth)
     c44f49f8a_l1_command_1_queued
     c44f49f8a_l2_withdrawal_cancelled
     c44f49f8a_l1_command_1_still_queued_after_cancel))
(define-fun report_safety () Bool (=> (and c44f49f8a_l2_withdrawal_cancelled
         c44f49f8a_l1_command_1_still_queued_after_cancel)
    (or (not c44f49f8a_l1_command_1_executed) (not c44f49f8a_l2_l1_desynced))))
(define-fun report_effects () Bool (and c44f49f8a_l2_withdrawal_cancelled
     c44f49f8a_l1_command_1_still_queued_after_cancel
     (not (or (not c44f49f8a_l1_command_1_executed)
              (not c44f49f8a_l2_l1_desynced)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
