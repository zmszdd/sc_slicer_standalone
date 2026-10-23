; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c83569d6f_lock_mode_after_rebase () Int)
(declare-fun c83569d6f_lock_mode_before_rebase () Int)
(declare-fun c83569d6f_rebase_clears_lockmode_occurred () Bool)
(assert
 (= c83569d6f_lock_mode_after_rebase c83569d6f_lock_mode_after_rebase))
(assert
 (= c83569d6f_lock_mode_before_rebase c83569d6f_lock_mode_before_rebase))
(assert
 (= c83569d6f_rebase_clears_lockmode_occurred c83569d6f_rebase_clears_lockmode_occurred))
(define-fun report_preconditions () Bool true)
(define-fun report_safety () Bool (=> c83569d6f_rebase_clears_lockmode_occurred
    (= c83569d6f_lock_mode_after_rebase c83569d6f_lock_mode_before_rebase)))
(define-fun report_effects () Bool c83569d6f_rebase_clears_lockmode_occurred)
(assert report_preconditions)
(check-sat)
(get-model)
