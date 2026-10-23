; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce56696fc_command1_queued () Bool)
(declare-fun ce56696fc_command1_remains_queued_after_cancel () Bool)
(declare-fun ce56696fc_command2_queued () Bool)
(declare-fun ce56696fc_l2_l1_desynchronized () Bool)
(declare-fun ce56696fc_staked_eth_amount () Int)
(assert
 (= ce56696fc_command1_queued ce56696fc_command1_queued))
(assert
 (= ce56696fc_command1_remains_queued_after_cancel ce56696fc_command1_remains_queued_after_cancel))
(assert
 (= ce56696fc_command2_queued ce56696fc_command2_queued))
(assert
 (= ce56696fc_l2_l1_desynchronized ce56696fc_l2_l1_desynchronized))
(assert
 (= ce56696fc_staked_eth_amount ce56696fc_staked_eth_amount))
(define-fun report_preconditions () Bool (and (= 1 ce56696fc_staked_eth_amount)
     ce56696fc_command1_queued
     ce56696fc_command1_remains_queued_after_cancel
     ce56696fc_command2_queued))
(define-fun report_safety () Bool (=> (and ce56696fc_command1_remains_queued_after_cancel
         ce56696fc_command2_queued)
    (not ce56696fc_l2_l1_desynchronized)))
(define-fun report_effects () Bool (and ce56696fc_command1_remains_queued_after_cancel
     ce56696fc_command2_queued
     (not (not ce56696fc_l2_l1_desynchronized))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
