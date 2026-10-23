; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc0ddd1a9_lock_mode_after_rebase () Int)
(declare-fun cc0ddd1a9_lock_mode_before_rebase () Int)
(assert
 (= cc0ddd1a9_lock_mode_after_rebase cc0ddd1a9_lock_mode_after_rebase))
(assert
 (= cc0ddd1a9_lock_mode_before_rebase cc0ddd1a9_lock_mode_before_rebase))
(define-fun report_preconditions () Bool (= 3 cc0ddd1a9_lock_mode_before_rebase))
(define-fun report_safety () Bool (=> (= 0 cc0ddd1a9_lock_mode_after_rebase)
    (=> (= 3 cc0ddd1a9_lock_mode_before_rebase)
        (= cc0ddd1a9_lock_mode_after_rebase cc0ddd1a9_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and (= 0 cc0ddd1a9_lock_mode_after_rebase)
     (= 3 cc0ddd1a9_lock_mode_before_rebase)
     (not (= cc0ddd1a9_lock_mode_after_rebase cc0ddd1a9_lock_mode_before_rebase))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
