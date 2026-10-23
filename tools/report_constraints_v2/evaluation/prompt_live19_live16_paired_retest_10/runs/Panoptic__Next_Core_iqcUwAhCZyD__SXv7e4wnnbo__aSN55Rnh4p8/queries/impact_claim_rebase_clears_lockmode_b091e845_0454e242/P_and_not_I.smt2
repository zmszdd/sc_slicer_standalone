; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6458cdc7_lock_mode_after_rebase () Int)
(declare-fun c6458cdc7_lock_mode_before_rebase () Int)
(declare-fun c6458cdc7_rebase_executed () Bool)
(assert
 (= c6458cdc7_lock_mode_after_rebase c6458cdc7_lock_mode_after_rebase))
(assert
 (= c6458cdc7_lock_mode_before_rebase c6458cdc7_lock_mode_before_rebase))
(assert
 (= c6458cdc7_rebase_executed c6458cdc7_rebase_executed))
(define-fun report_preconditions () Bool true)
(define-fun report_safety () Bool (=> c6458cdc7_rebase_executed
    (=> c6458cdc7_rebase_executed
        (= c6458cdc7_lock_mode_after_rebase c6458cdc7_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and c6458cdc7_rebase_executed
     c6458cdc7_rebase_executed
     (not (= c6458cdc7_lock_mode_after_rebase c6458cdc7_lock_mode_before_rebase))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
