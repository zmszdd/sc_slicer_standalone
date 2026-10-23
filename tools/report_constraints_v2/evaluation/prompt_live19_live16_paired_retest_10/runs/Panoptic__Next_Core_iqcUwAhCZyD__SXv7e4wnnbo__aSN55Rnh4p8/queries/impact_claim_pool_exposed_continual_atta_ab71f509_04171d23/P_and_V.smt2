; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd2af2335_caller_is_guardian () Bool)
(declare-fun cd2af2335_lock_mode_before () Int)
(declare-fun cd2af2335_pool_exposed_continual_attack_occurs () Bool)
(declare-fun cd2af2335_unlock_pool_performed () Bool)
(assert
 (= cd2af2335_caller_is_guardian cd2af2335_caller_is_guardian))
(assert
 (= cd2af2335_lock_mode_before cd2af2335_lock_mode_before))
(assert
 (= cd2af2335_pool_exposed_continual_attack_occurs cd2af2335_pool_exposed_continual_attack_occurs))
(assert
 (= cd2af2335_unlock_pool_performed cd2af2335_unlock_pool_performed))
(define-fun report_preconditions () Bool (= 3 cd2af2335_lock_mode_before))
(define-fun report_safety () Bool (=> cd2af2335_pool_exposed_continual_attack_occurs
    (=> cd2af2335_unlock_pool_performed cd2af2335_caller_is_guardian)))
(define-fun report_effects () Bool (and cd2af2335_pool_exposed_continual_attack_occurs
     cd2af2335_unlock_pool_performed
     (not cd2af2335_caller_is_guardian)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
