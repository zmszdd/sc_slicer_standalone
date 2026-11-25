; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c9ba23fa6_correct_recipient () ReportAddress)
(declare-fun c9ba23fa6_distribute_assets_recipient () ReportAddress)
(declare-fun c9ba23fa6_launchpad_cannot_recover_tokens () Bool)
(declare-fun c9ba23fa6_rewards_permanently_lost () Bool)
(declare-fun c9ba23fa6_user_has_pending_rewards () Bool)
(declare-fun c9ba23fa6_user_holds_tokens_bonding_phase () Bool)
(assert
 (= c9ba23fa6_correct_recipient c9ba23fa6_correct_recipient))
(assert
 (= c9ba23fa6_distribute_assets_recipient c9ba23fa6_distribute_assets_recipient))
(assert
 (= c9ba23fa6_launchpad_cannot_recover_tokens c9ba23fa6_launchpad_cannot_recover_tokens))
(assert
 (= c9ba23fa6_rewards_permanently_lost c9ba23fa6_rewards_permanently_lost))
(assert
 (= c9ba23fa6_user_has_pending_rewards c9ba23fa6_user_has_pending_rewards))
(assert
 (= c9ba23fa6_user_holds_tokens_bonding_phase c9ba23fa6_user_holds_tokens_bonding_phase))
(define-fun report_preconditions () Bool (and c9ba23fa6_user_holds_tokens_bonding_phase
     c9ba23fa6_user_has_pending_rewards
     c9ba23fa6_launchpad_cannot_recover_tokens))
(define-fun report_safety () Bool (=> c9ba23fa6_user_has_pending_rewards
    (= c9ba23fa6_distribute_assets_recipient c9ba23fa6_correct_recipient)))
(define-fun report_effects () Bool (and c9ba23fa6_user_has_pending_rewards
     (not (= c9ba23fa6_distribute_assets_recipient c9ba23fa6_correct_recipient))
     c9ba23fa6_rewards_permanently_lost
     c9ba23fa6_rewards_permanently_lost))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
