; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c50389ebd_controller_in_active_set () Bool)
(declare-fun c50389ebd_first_request_fulfilled_occurred () Bool)
(declare-fun c50389ebd_pending_redeem_shares () Int)
(declare-fun c50389ebd_second_request_submitted () Bool)
(declare-fun c50389ebd_vault_unregistered () Bool)
(declare-fun c50389ebd_zero_shares () Int)
(assert
 (= c50389ebd_controller_in_active_set c50389ebd_controller_in_active_set))
(assert
 (= c50389ebd_first_request_fulfilled_occurred c50389ebd_first_request_fulfilled_occurred))
(assert
 (= c50389ebd_pending_redeem_shares c50389ebd_pending_redeem_shares))
(assert
 (= c50389ebd_second_request_submitted c50389ebd_second_request_submitted))
(assert
 (= c50389ebd_vault_unregistered c50389ebd_vault_unregistered))
(assert
 (= c50389ebd_zero_shares c50389ebd_zero_shares))
(define-fun report_preconditions () Bool (and c50389ebd_controller_in_active_set
     c50389ebd_first_request_fulfilled_occurred
     c50389ebd_second_request_submitted
     (distinct c50389ebd_pending_redeem_shares c50389ebd_zero_shares)))
(define-fun report_safety () Bool (=> (and c50389ebd_second_request_submitted
         (distinct c50389ebd_pending_redeem_shares c50389ebd_zero_shares))
    (not c50389ebd_vault_unregistered)))
(define-fun report_effects () Bool (and c50389ebd_second_request_submitted
     (distinct c50389ebd_pending_redeem_shares c50389ebd_zero_shares)
     (not (not c50389ebd_vault_unregistered))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
