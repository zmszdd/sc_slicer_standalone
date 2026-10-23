; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0d7ec5fc_end_rewards_completed () Bool)
(declare-fun c0d7ec5fc_end_rewards_reverted () Bool)
(declare-fun c0d7ec5fc_pair_created_with_salt_occurred () Bool)
(declare-fun c0d7ec5fc_pairfor_computed () Bool)
(assert
 (= c0d7ec5fc_end_rewards_completed c0d7ec5fc_end_rewards_completed))
(assert
 (= c0d7ec5fc_end_rewards_reverted c0d7ec5fc_end_rewards_reverted))
(assert
 (= c0d7ec5fc_pair_created_with_salt_occurred c0d7ec5fc_pair_created_with_salt_occurred))
(assert
 (= c0d7ec5fc_pairfor_computed c0d7ec5fc_pairfor_computed))
(define-fun report_preconditions () Bool (and c0d7ec5fc_pair_created_with_salt_occurred c0d7ec5fc_pairfor_computed))
(define-fun report_safety () Bool (=> (and c0d7ec5fc_pair_created_with_salt_occurred c0d7ec5fc_pairfor_computed)
    (and c0d7ec5fc_end_rewards_completed (not c0d7ec5fc_end_rewards_reverted))))
(define-fun report_effects () Bool (and c0d7ec5fc_pair_created_with_salt_occurred
     c0d7ec5fc_pairfor_computed
     (not (and c0d7ec5fc_end_rewards_completed
               (not c0d7ec5fc_end_rewards_reverted)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
