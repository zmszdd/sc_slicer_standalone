; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdff7982a_controller_in_active_set () Bool)
(declare-fun cdff7982a_first_request_fulfilled_occurred () Bool)
(declare-fun cdff7982a_pending_redeem_shares () Int)
(declare-fun cdff7982a_second_request_submitted () Bool)
(declare-fun cdff7982a_shares_stuck_occurred () Bool)
(declare-fun cdff7982a_vault_unregistered () Bool)
(declare-fun cdff7982a_zero_shares () Int)
(assert
 (= cdff7982a_controller_in_active_set cdff7982a_controller_in_active_set))
(assert
 (= cdff7982a_first_request_fulfilled_occurred cdff7982a_first_request_fulfilled_occurred))
(assert
 (= cdff7982a_pending_redeem_shares cdff7982a_pending_redeem_shares))
(assert
 (= cdff7982a_second_request_submitted cdff7982a_second_request_submitted))
(assert
 (= cdff7982a_shares_stuck_occurred cdff7982a_shares_stuck_occurred))
(assert
 (= cdff7982a_vault_unregistered cdff7982a_vault_unregistered))
(assert
 (= cdff7982a_zero_shares cdff7982a_zero_shares))
(define-fun report_preconditions () Bool (and cdff7982a_controller_in_active_set
     cdff7982a_first_request_fulfilled_occurred
     cdff7982a_second_request_submitted
     (distinct cdff7982a_pending_redeem_shares cdff7982a_zero_shares)))
(define-fun report_safety () Bool (=> (and (distinct cdff7982a_pending_redeem_shares cdff7982a_zero_shares)
         cdff7982a_vault_unregistered)
    (and (not cdff7982a_vault_unregistered)
         (not cdff7982a_shares_stuck_occurred))))
(define-fun report_effects () Bool (and (distinct cdff7982a_pending_redeem_shares cdff7982a_zero_shares)
     cdff7982a_vault_unregistered
     (not (and (not cdff7982a_vault_unregistered)
               (not cdff7982a_shares_stuck_occurred)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
