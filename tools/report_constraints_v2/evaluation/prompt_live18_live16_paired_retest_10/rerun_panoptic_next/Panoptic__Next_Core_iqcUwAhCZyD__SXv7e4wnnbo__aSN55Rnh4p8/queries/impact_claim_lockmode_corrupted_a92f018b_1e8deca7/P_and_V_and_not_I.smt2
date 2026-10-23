; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9f6e76ab_lock_mode_after_rebase () Int)
(declare-fun c9f6e76ab_lock_mode_before_rebase () Int)
(declare-fun c9f6e76ab_rebase_executed () Bool)
(assert
 (= c9f6e76ab_lock_mode_after_rebase c9f6e76ab_lock_mode_after_rebase))
(assert
 (= c9f6e76ab_lock_mode_before_rebase c9f6e76ab_lock_mode_before_rebase))
(assert
 (= c9f6e76ab_rebase_executed c9f6e76ab_rebase_executed))
(define-fun report_preconditions () Bool true)
(define-fun report_safety () Bool (=> c9f6e76ab_rebase_executed
    (=> c9f6e76ab_rebase_executed
        (= c9f6e76ab_lock_mode_after_rebase c9f6e76ab_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and c9f6e76ab_rebase_executed
     c9f6e76ab_rebase_executed
     (not (= c9f6e76ab_lock_mode_after_rebase c9f6e76ab_lock_mode_before_rebase))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
