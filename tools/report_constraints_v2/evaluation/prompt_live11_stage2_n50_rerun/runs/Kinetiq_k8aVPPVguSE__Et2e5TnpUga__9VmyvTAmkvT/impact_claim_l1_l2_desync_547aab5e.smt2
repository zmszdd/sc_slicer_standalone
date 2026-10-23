; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44f49f8a_cancelled_before_processing () Bool)
(declare-fun c44f49f8a_command_1_still_queued_after_cancel () Bool)
(declare-fun c44f49f8a_l2_l1_desync () Bool)
(declare-fun c44f49f8a_queued_command_1_present () Bool)
(declare-fun c44f49f8a_requeued_command_2_present () Bool)
(declare-fun c44f49f8a_staked_eth_amount () Int)
(assert
 (= c44f49f8a_cancelled_before_processing c44f49f8a_cancelled_before_processing))
(assert
 (= c44f49f8a_command_1_still_queued_after_cancel c44f49f8a_command_1_still_queued_after_cancel))
(assert
 (= c44f49f8a_l2_l1_desync c44f49f8a_l2_l1_desync))
(assert
 (= c44f49f8a_queued_command_1_present c44f49f8a_queued_command_1_present))
(assert
 (= c44f49f8a_requeued_command_2_present c44f49f8a_requeued_command_2_present))
(assert
 (= c44f49f8a_staked_eth_amount c44f49f8a_staked_eth_amount))
(define-fun report_preconditions () Bool (and (= 1 c44f49f8a_staked_eth_amount)
     c44f49f8a_queued_command_1_present
     c44f49f8a_cancelled_before_processing
     c44f49f8a_requeued_command_2_present))
(define-fun report_safety () Bool (=> (and c44f49f8a_cancelled_before_processing
         c44f49f8a_command_1_still_queued_after_cancel)
    (not c44f49f8a_l2_l1_desync)))
(define-fun report_effects () Bool (and c44f49f8a_cancelled_before_processing
     c44f49f8a_command_1_still_queued_after_cancel
     (not (not c44f49f8a_l2_l1_desync))))
