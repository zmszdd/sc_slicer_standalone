; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd7fded92_auto_borrow_occurred () Bool)
(declare-fun cd7fded92_pm_enabled () Bool)
(declare-fun cd7fded92_settle_accepted_unbacked_yield () Bool)
(declare-fun cd7fded92_vault_has_l1_position () Bool)
(assert
 (= cd7fded92_auto_borrow_occurred cd7fded92_auto_borrow_occurred))
(assert
 (= cd7fded92_pm_enabled cd7fded92_pm_enabled))
(assert
 (= cd7fded92_settle_accepted_unbacked_yield cd7fded92_settle_accepted_unbacked_yield))
(assert
 (= cd7fded92_vault_has_l1_position cd7fded92_vault_has_l1_position))
(define-fun report_preconditions () Bool (and cd7fded92_pm_enabled
     cd7fded92_vault_has_l1_position
     cd7fded92_auto_borrow_occurred))
(define-fun report_safety () Bool (=> cd7fded92_settle_accepted_unbacked_yield
    (not cd7fded92_settle_accepted_unbacked_yield)))
(define-fun report_effects () Bool (and cd7fded92_settle_accepted_unbacked_yield
     (not (not cd7fded92_settle_accepted_unbacked_yield))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
