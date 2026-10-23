; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44f49f8a_cancelled_before_processing () Bool)
(declare-fun c44f49f8a_l1_undelegate_operation_queued () Bool)
(declare-fun c44f49f8a_l2_l1_state_desynced () Bool)
(declare-fun c44f49f8a_l2_withdrawal_request_exists () Bool)
(declare-fun c44f49f8a_staked_amount () Int)
(assert
 (= c44f49f8a_cancelled_before_processing c44f49f8a_cancelled_before_processing))
(assert
 (= c44f49f8a_l1_undelegate_operation_queued c44f49f8a_l1_undelegate_operation_queued))
(assert
 (= c44f49f8a_l2_l1_state_desynced c44f49f8a_l2_l1_state_desynced))
(assert
 (= c44f49f8a_l2_withdrawal_request_exists c44f49f8a_l2_withdrawal_request_exists))
(assert
 (= c44f49f8a_staked_amount c44f49f8a_staked_amount))
(define-fun report_preconditions () Bool (and (= 1 c44f49f8a_staked_amount)
     c44f49f8a_l2_withdrawal_request_exists
     c44f49f8a_cancelled_before_processing))
(define-fun report_safety () Bool (=> (and c44f49f8a_l2_withdrawal_request_exists
         c44f49f8a_cancelled_before_processing)
    (and (not c44f49f8a_l1_undelegate_operation_queued)
         (not c44f49f8a_l2_l1_state_desynced))))
(define-fun report_effects () Bool (and c44f49f8a_l2_withdrawal_request_exists
     c44f49f8a_cancelled_before_processing
     (not (and (not c44f49f8a_l1_undelegate_operation_queued)
               (not c44f49f8a_l2_l1_state_desynced)))))
