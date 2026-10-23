; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cab1ac6b0_accounting_reads_revert () Bool)
(declare-fun cab1ac6b0_blp_reserve_exists () Bool)
(declare-fun cab1ac6b0_pm_active () Bool)
(assert
 (= cab1ac6b0_accounting_reads_revert cab1ac6b0_accounting_reads_revert))
(assert
 (= cab1ac6b0_blp_reserve_exists cab1ac6b0_blp_reserve_exists))
(assert
 (= cab1ac6b0_pm_active cab1ac6b0_pm_active))
(define-fun report_preconditions () Bool (and cab1ac6b0_pm_active (not cab1ac6b0_blp_reserve_exists)))
(define-fun report_safety () Bool (=> (and cab1ac6b0_pm_active (not cab1ac6b0_blp_reserve_exists))
    (not cab1ac6b0_accounting_reads_revert)))
(define-fun report_effects () Bool (and cab1ac6b0_pm_active
     (not cab1ac6b0_blp_reserve_exists)
     (not (not cab1ac6b0_accounting_reads_revert))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
