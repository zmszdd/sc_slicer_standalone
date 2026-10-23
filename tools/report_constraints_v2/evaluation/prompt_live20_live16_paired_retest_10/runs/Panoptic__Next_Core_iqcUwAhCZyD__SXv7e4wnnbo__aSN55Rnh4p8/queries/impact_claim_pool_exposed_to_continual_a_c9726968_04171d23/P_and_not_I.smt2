; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6452479f_lock_mode_before () Int)
(declare-fun c6452479f_pool_exposed_to_continual_attack_occurred () Bool)
(declare-fun c6452479f_rebase_oracle_pack_performed_unlock () Bool)
(assert
 (= c6452479f_lock_mode_before c6452479f_lock_mode_before))
(assert
 (= c6452479f_pool_exposed_to_continual_attack_occurred c6452479f_pool_exposed_to_continual_attack_occurred))
(assert
 (= c6452479f_rebase_oracle_pack_performed_unlock c6452479f_rebase_oracle_pack_performed_unlock))
(define-fun report_preconditions () Bool (= 3 c6452479f_lock_mode_before))
(define-fun report_safety () Bool (=> c6452479f_rebase_oracle_pack_performed_unlock
    (not c6452479f_rebase_oracle_pack_performed_unlock)))
(define-fun report_effects () Bool c6452479f_pool_exposed_to_continual_attack_occurred)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
