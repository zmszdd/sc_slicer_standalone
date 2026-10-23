; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7b5c8e7f_lock_mode_after_rebase () Int)
(declare-fun c7b5c8e7f_lock_mode_before_rebase () Int)
(declare-fun c7b5c8e7f_pool_exposed_for_continual_attack_occurred () Bool)
(assert
 (= c7b5c8e7f_lock_mode_after_rebase c7b5c8e7f_lock_mode_after_rebase))
(assert
 (= c7b5c8e7f_lock_mode_before_rebase c7b5c8e7f_lock_mode_before_rebase))
(assert
 (= c7b5c8e7f_pool_exposed_for_continual_attack_occurred c7b5c8e7f_pool_exposed_for_continual_attack_occurred))
(define-fun report_preconditions () Bool (= 3 c7b5c8e7f_lock_mode_before_rebase))
(define-fun report_safety () Bool (=> c7b5c8e7f_pool_exposed_for_continual_attack_occurred
    (=> (= 3 c7b5c8e7f_lock_mode_before_rebase)
        (= c7b5c8e7f_lock_mode_after_rebase c7b5c8e7f_lock_mode_before_rebase))))
(define-fun report_effects () Bool (and c7b5c8e7f_pool_exposed_for_continual_attack_occurred
     (= 3 c7b5c8e7f_lock_mode_before_rebase)
     (not (= c7b5c8e7f_lock_mode_after_rebase c7b5c8e7f_lock_mode_before_rebase))))
