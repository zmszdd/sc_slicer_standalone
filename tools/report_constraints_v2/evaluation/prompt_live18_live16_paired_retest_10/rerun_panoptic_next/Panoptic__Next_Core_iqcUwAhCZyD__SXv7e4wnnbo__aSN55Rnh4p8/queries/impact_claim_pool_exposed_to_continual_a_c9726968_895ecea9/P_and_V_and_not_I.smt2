; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c875fc8f1_caller_is_guardian () Bool)
(declare-fun c875fc8f1_lock_mode_before () Int)
(declare-fun c875fc8f1_pool_unlocked_by_rebase () Bool)
(assert
 (= c875fc8f1_caller_is_guardian c875fc8f1_caller_is_guardian))
(assert
 (= c875fc8f1_lock_mode_before c875fc8f1_lock_mode_before))
(assert
 (= c875fc8f1_pool_unlocked_by_rebase c875fc8f1_pool_unlocked_by_rebase))
(define-fun report_preconditions () Bool (= 3 c875fc8f1_lock_mode_before))
(define-fun report_safety () Bool (=> c875fc8f1_pool_unlocked_by_rebase
    (=> c875fc8f1_pool_unlocked_by_rebase c875fc8f1_caller_is_guardian)))
(define-fun report_effects () Bool (and c875fc8f1_pool_unlocked_by_rebase
     c875fc8f1_pool_unlocked_by_rebase
     (not c875fc8f1_caller_is_guardian)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
