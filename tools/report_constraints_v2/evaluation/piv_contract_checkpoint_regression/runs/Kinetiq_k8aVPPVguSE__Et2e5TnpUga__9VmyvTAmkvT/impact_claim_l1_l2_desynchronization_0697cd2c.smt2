; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1cf3e452_cancelled_undelegate_executed () Bool)
(declare-fun c1cf3e452_l1_command_1_queued () Bool)
(declare-fun c1cf3e452_l1_command_1_remains_queued_after_cancel () Bool)
(declare-fun c1cf3e452_l1_command_2_queued () Bool)
(declare-fun c1cf3e452_l2_state_desynchronized_from_l1 () Bool)
(declare-fun c1cf3e452_staked_eth_amount () Int)
(assert
 (= c1cf3e452_cancelled_undelegate_executed c1cf3e452_cancelled_undelegate_executed))
(assert
 (= c1cf3e452_l1_command_1_queued c1cf3e452_l1_command_1_queued))
(assert
 (= c1cf3e452_l1_command_1_remains_queued_after_cancel c1cf3e452_l1_command_1_remains_queued_after_cancel))
(assert
 (= c1cf3e452_l1_command_2_queued c1cf3e452_l1_command_2_queued))
(assert
 (= c1cf3e452_l2_state_desynchronized_from_l1 c1cf3e452_l2_state_desynchronized_from_l1))
(assert
 (= c1cf3e452_staked_eth_amount c1cf3e452_staked_eth_amount))
(define-fun report_preconditions () Bool (and (= 1 c1cf3e452_staked_eth_amount)
     c1cf3e452_l1_command_1_queued
     c1cf3e452_l1_command_1_remains_queued_after_cancel
     c1cf3e452_l1_command_2_queued))
(define-fun report_safety () Bool (=> (and (= 1 c1cf3e452_staked_eth_amount)
         c1cf3e452_l1_command_1_queued
         c1cf3e452_l1_command_1_remains_queued_after_cancel
         c1cf3e452_l1_command_2_queued)
    (or (not c1cf3e452_cancelled_undelegate_executed)
        (not c1cf3e452_l2_state_desynchronized_from_l1))))
(define-fun report_effects () Bool (and (= 1 c1cf3e452_staked_eth_amount)
     c1cf3e452_l1_command_1_queued
     c1cf3e452_l1_command_1_remains_queued_after_cancel
     c1cf3e452_l1_command_2_queued
     (not (or (not c1cf3e452_cancelled_undelegate_executed)
              (not c1cf3e452_l2_state_desynchronized_from_l1)))))
