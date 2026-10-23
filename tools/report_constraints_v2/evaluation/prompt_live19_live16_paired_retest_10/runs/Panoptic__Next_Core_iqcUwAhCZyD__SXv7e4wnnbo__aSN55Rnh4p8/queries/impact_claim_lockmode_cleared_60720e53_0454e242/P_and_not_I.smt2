; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c635ae4c8_lock_mode_after_rebase () Int)
(declare-fun c635ae4c8_lock_mode_before_rebase () Int)
(declare-fun c635ae4c8_rebase_executed () Bool)
(assert
 (= c635ae4c8_lock_mode_after_rebase c635ae4c8_lock_mode_after_rebase))
(assert
 (= c635ae4c8_lock_mode_before_rebase c635ae4c8_lock_mode_before_rebase))
(assert
 (= c635ae4c8_rebase_executed c635ae4c8_rebase_executed))
(define-fun report_preconditions () Bool true)
(define-fun report_safety () Bool (=> (and c635ae4c8_rebase_executed (= 0 c635ae4c8_lock_mode_after_rebase))
    (=> c635ae4c8_rebase_executed
        (= c635ae4c8_lock_mode_after_rebase c635ae4c8_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and c635ae4c8_rebase_executed
     (= 0 c635ae4c8_lock_mode_after_rebase)
     c635ae4c8_rebase_executed
     (not (= c635ae4c8_lock_mode_after_rebase c635ae4c8_lock_mode_before_rebase))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
