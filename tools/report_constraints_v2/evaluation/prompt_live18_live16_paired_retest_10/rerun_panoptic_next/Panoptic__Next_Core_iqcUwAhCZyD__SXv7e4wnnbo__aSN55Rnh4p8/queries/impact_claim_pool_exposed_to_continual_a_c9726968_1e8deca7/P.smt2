; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc3806d91_lock_mode_after_rebase () Int)
(declare-fun cc3806d91_lock_mode_before_rebase () Int)
(declare-fun cc3806d91_rebase_executed () Bool)
(assert
 (= cc3806d91_lock_mode_after_rebase cc3806d91_lock_mode_after_rebase))
(assert
 (= cc3806d91_lock_mode_before_rebase cc3806d91_lock_mode_before_rebase))
(assert
 (= cc3806d91_rebase_executed cc3806d91_rebase_executed))
(define-fun report_preconditions () Bool (= 3 cc3806d91_lock_mode_before_rebase))
(define-fun report_safety () Bool (=> (distinct 3 cc3806d91_lock_mode_after_rebase)
    (=> cc3806d91_rebase_executed
        (= cc3806d91_lock_mode_after_rebase cc3806d91_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and (distinct 3 cc3806d91_lock_mode_after_rebase)
     cc3806d91_rebase_executed
     (not (= cc3806d91_lock_mode_after_rebase cc3806d91_lock_mode_before_rebase))))
(assert report_preconditions)
(check-sat)
(get-model)
