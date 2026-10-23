; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44f49f8a_l1_command_1_queued () Bool)
(declare-fun c44f49f8a_l1_command_1_still_queued () Bool)
(declare-fun c44f49f8a_l2_l1_state_desynced () Bool)
(declare-fun c44f49f8a_staked_eth_amount () Int)
(declare-fun c44f49f8a_withdrawal_cancelled_before_processing () Bool)
(assert
 (= c44f49f8a_l1_command_1_queued c44f49f8a_l1_command_1_queued))
(assert
 (= c44f49f8a_l1_command_1_still_queued c44f49f8a_l1_command_1_still_queued))
(assert
 (= c44f49f8a_l2_l1_state_desynced c44f49f8a_l2_l1_state_desynced))
(assert
 (= c44f49f8a_staked_eth_amount c44f49f8a_staked_eth_amount))
(assert
 (= c44f49f8a_withdrawal_cancelled_before_processing c44f49f8a_withdrawal_cancelled_before_processing))
(define-fun report_preconditions () Bool (and (= 1 c44f49f8a_staked_eth_amount)
     c44f49f8a_l1_command_1_queued
     c44f49f8a_withdrawal_cancelled_before_processing
     c44f49f8a_l1_command_1_still_queued))
(define-fun report_safety () Bool (=> (and c44f49f8a_withdrawal_cancelled_before_processing
         c44f49f8a_l1_command_1_still_queued)
    (not c44f49f8a_l2_l1_state_desynced)))
(define-fun report_effects () Bool (and c44f49f8a_withdrawal_cancelled_before_processing
     c44f49f8a_l1_command_1_still_queued
     (not (not c44f49f8a_l2_l1_state_desynced))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
