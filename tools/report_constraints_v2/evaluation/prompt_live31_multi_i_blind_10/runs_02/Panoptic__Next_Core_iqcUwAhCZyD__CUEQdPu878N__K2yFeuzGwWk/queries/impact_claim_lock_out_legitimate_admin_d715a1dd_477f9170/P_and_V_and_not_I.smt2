; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccb83ff8e_admin_locked_out () Bool)
(declare-fun ccb83ff8e_admin_privileges_retained () Bool)
(declare-fun ccb83ff8e_wallet_deployed_by_factory_occurred () Bool)
(assert
 (= ccb83ff8e_admin_locked_out ccb83ff8e_admin_locked_out))
(assert
 (= ccb83ff8e_admin_privileges_retained ccb83ff8e_admin_privileges_retained))
(assert
 (= ccb83ff8e_wallet_deployed_by_factory_occurred ccb83ff8e_wallet_deployed_by_factory_occurred))
(define-fun report_preconditions () Bool ccb83ff8e_wallet_deployed_by_factory_occurred)
(define-fun report_safety () Bool (=> ccb83ff8e_admin_locked_out
    (=> ccb83ff8e_admin_privileges_retained (not ccb83ff8e_admin_locked_out))))
(define-fun report_effects () Bool (and ccb83ff8e_admin_locked_out
     ccb83ff8e_admin_privileges_retained
     (not (not ccb83ff8e_admin_locked_out))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
