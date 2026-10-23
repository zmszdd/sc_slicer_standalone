; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8dbe132a_lock_mode_after_rebase () Int)
(declare-fun c8dbe132a_lock_mode_before_rebase () Int)
(declare-fun c8dbe132a_lock_mode_corrupted_after_rebase () Bool)
(assert
 (= c8dbe132a_lock_mode_after_rebase c8dbe132a_lock_mode_after_rebase))
(assert
 (= c8dbe132a_lock_mode_before_rebase c8dbe132a_lock_mode_before_rebase))
(assert
 (= c8dbe132a_lock_mode_corrupted_after_rebase c8dbe132a_lock_mode_corrupted_after_rebase))
(define-fun report_preconditions () Bool (= 3 c8dbe132a_lock_mode_before_rebase))
(define-fun report_safety () Bool (=> c8dbe132a_lock_mode_corrupted_after_rebase
    (=> (= 3 c8dbe132a_lock_mode_before_rebase)
        (= c8dbe132a_lock_mode_after_rebase c8dbe132a_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and c8dbe132a_lock_mode_corrupted_after_rebase
     (= 3 c8dbe132a_lock_mode_before_rebase)
     (not (= c8dbe132a_lock_mode_after_rebase c8dbe132a_lock_mode_before_rebase))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
