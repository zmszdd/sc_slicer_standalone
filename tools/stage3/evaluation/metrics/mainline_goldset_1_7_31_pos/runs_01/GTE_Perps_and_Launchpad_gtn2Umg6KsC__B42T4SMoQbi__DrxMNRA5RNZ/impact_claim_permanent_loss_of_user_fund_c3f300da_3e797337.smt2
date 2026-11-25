; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cadf088b3_correct_recipient () ReportAddress)
(declare-fun cadf088b3_distribute_assets_recipient () ReportAddress)
(declare-fun cadf088b3_launchpad_cannot_recover_tokens () Bool)
(declare-fun cadf088b3_user_funds_permanently_lost () Bool)
(declare-fun cadf088b3_user_has_pending_rewards () Bool)
(declare-fun cadf088b3_user_holds_launched_tokens () Bool)
(assert
 (= cadf088b3_correct_recipient cadf088b3_correct_recipient))
(assert
 (= cadf088b3_distribute_assets_recipient cadf088b3_distribute_assets_recipient))
(assert
 (= cadf088b3_launchpad_cannot_recover_tokens cadf088b3_launchpad_cannot_recover_tokens))
(assert
 (= cadf088b3_user_funds_permanently_lost cadf088b3_user_funds_permanently_lost))
(assert
 (= cadf088b3_user_has_pending_rewards cadf088b3_user_has_pending_rewards))
(assert
 (= cadf088b3_user_holds_launched_tokens cadf088b3_user_holds_launched_tokens))
(define-fun report_preconditions () Bool (and cadf088b3_user_holds_launched_tokens
     cadf088b3_user_has_pending_rewards
     cadf088b3_launchpad_cannot_recover_tokens))
(define-fun report_safety () Bool (=> cadf088b3_user_has_pending_rewards
    (= cadf088b3_distribute_assets_recipient cadf088b3_correct_recipient)))
(define-fun report_effects () Bool (and cadf088b3_user_has_pending_rewards
     (not (= cadf088b3_distribute_assets_recipient cadf088b3_correct_recipient))
     cadf088b3_user_funds_permanently_lost
     cadf088b3_user_funds_permanently_lost))
