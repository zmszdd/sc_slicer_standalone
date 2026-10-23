; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c90cecab9_griefing_enabled () Bool)
(declare-fun c90cecab9_no_reentrancy_guard_present () Bool)
(declare-fun c90cecab9_pending_accounting_increased_before_transfer () Bool)
(declare-fun c90cecab9_reentrant_entrypoint_invoked () Bool)
(assert
 (= c90cecab9_griefing_enabled c90cecab9_griefing_enabled))
(assert
 (= c90cecab9_no_reentrancy_guard_present c90cecab9_no_reentrancy_guard_present))
(assert
 (= c90cecab9_pending_accounting_increased_before_transfer c90cecab9_pending_accounting_increased_before_transfer))
(assert
 (= c90cecab9_reentrant_entrypoint_invoked c90cecab9_reentrant_entrypoint_invoked))
(define-fun report_preconditions () Bool c90cecab9_no_reentrancy_guard_present)
(define-fun report_safety () Bool (=> c90cecab9_pending_accounting_increased_before_transfer
    (not c90cecab9_reentrant_entrypoint_invoked)))
(define-fun report_effects () Bool c90cecab9_griefing_enabled)
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
