; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd7fded92_auto_borrow_occurred () Bool)
(declare-fun cd7fded92_phantom_surplus_passes_gate3 () Bool)
(declare-fun cd7fded92_pm_active () Bool)
(assert
 (= cd7fded92_auto_borrow_occurred cd7fded92_auto_borrow_occurred))
(assert
 (= cd7fded92_phantom_surplus_passes_gate3 cd7fded92_phantom_surplus_passes_gate3))
(assert
 (= cd7fded92_pm_active cd7fded92_pm_active))
(define-fun report_preconditions () Bool (and cd7fded92_pm_active cd7fded92_auto_borrow_occurred))
(define-fun report_safety () Bool (=> (and cd7fded92_pm_active cd7fded92_auto_borrow_occurred)
    (not cd7fded92_phantom_surplus_passes_gate3)))
(define-fun report_effects () Bool (and cd7fded92_pm_active
     cd7fded92_auto_borrow_occurred
     (not (not cd7fded92_phantom_surplus_passes_gate3))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
