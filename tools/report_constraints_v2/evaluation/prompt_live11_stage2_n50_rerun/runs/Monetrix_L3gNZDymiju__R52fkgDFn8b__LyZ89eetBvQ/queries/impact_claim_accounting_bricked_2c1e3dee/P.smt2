; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2f557382_accounting_reads_revert () Bool)
(declare-fun c2f557382_blp_reserve_exists () Bool)
(declare-fun c2f557382_pm_active () Bool)
(assert
 (= c2f557382_accounting_reads_revert c2f557382_accounting_reads_revert))
(assert
 (= c2f557382_blp_reserve_exists c2f557382_blp_reserve_exists))
(assert
 (= c2f557382_pm_active c2f557382_pm_active))
(define-fun report_preconditions () Bool (and c2f557382_pm_active (not c2f557382_blp_reserve_exists)))
(define-fun report_safety () Bool (=> (and c2f557382_pm_active (not c2f557382_blp_reserve_exists))
    (not c2f557382_accounting_reads_revert)))
(define-fun report_effects () Bool (and c2f557382_pm_active
     (not c2f557382_blp_reserve_exists)
     (not (not c2f557382_accounting_reads_revert))))
(assert report_preconditions)
(check-sat)
(get-model)
