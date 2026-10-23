; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd946fd9f_permanent_loss_of_access_to_user_funds () Bool)
(declare-fun cd946fd9f_request_retrievable_via_standard_functions () Bool)
(declare-fun cd946fd9f_user_has_pending_request_in_epoch_e () Bool)
(assert
 (= cd946fd9f_permanent_loss_of_access_to_user_funds cd946fd9f_permanent_loss_of_access_to_user_funds))
(assert
 (= cd946fd9f_request_retrievable_via_standard_functions cd946fd9f_request_retrievable_via_standard_functions))
(assert
 (= cd946fd9f_user_has_pending_request_in_epoch_e cd946fd9f_user_has_pending_request_in_epoch_e))
(define-fun report_preconditions () Bool cd946fd9f_user_has_pending_request_in_epoch_e)
(define-fun report_safety () Bool (=> cd946fd9f_permanent_loss_of_access_to_user_funds
    (=> cd946fd9f_user_has_pending_request_in_epoch_e
        cd946fd9f_request_retrievable_via_standard_functions)))
(define-fun report_effects () Bool (and cd946fd9f_permanent_loss_of_access_to_user_funds
     cd946fd9f_user_has_pending_request_in_epoch_e
     (not cd946fd9f_request_retrievable_via_standard_functions)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
