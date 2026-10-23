; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c171a28cb_lock_mode_after_rebase () Int)
(declare-fun c171a28cb_lock_mode_before_rebase () Int)
(declare-fun c171a28cb_rebase_executed () Bool)
(assert
 (= c171a28cb_lock_mode_after_rebase c171a28cb_lock_mode_after_rebase))
(assert
 (= c171a28cb_lock_mode_before_rebase c171a28cb_lock_mode_before_rebase))
(assert
 (= c171a28cb_rebase_executed c171a28cb_rebase_executed))
(define-fun report_preconditions () Bool true)
(define-fun report_safety () Bool (=> c171a28cb_rebase_executed
    (= c171a28cb_lock_mode_after_rebase c171a28cb_lock_mode_before_rebase)))
(define-fun report_effects () Bool (and (= 0 c171a28cb_lock_mode_after_rebase) c171a28cb_rebase_executed))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
