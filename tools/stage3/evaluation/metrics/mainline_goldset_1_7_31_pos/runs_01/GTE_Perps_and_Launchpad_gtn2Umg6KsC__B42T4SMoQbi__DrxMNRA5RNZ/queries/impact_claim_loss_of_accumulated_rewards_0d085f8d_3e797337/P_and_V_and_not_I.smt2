; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c6d075b7f_distribute_assets_recipient () ReportAddress)
(declare-fun c6d075b7f_intended_recipient () ReportAddress)
(declare-fun c6d075b7f_launchpad_can_recover_tokens () Bool)
(declare-fun c6d075b7f_rewards_lost_on_buy_or_sell () Bool)
(declare-fun c6d075b7f_user_holds_launched_tokens () Bool)
(declare-fun c6d075b7f_user_pending_rewards () Int)
(assert
 (= c6d075b7f_distribute_assets_recipient c6d075b7f_distribute_assets_recipient))
(assert
 (= c6d075b7f_intended_recipient c6d075b7f_intended_recipient))
(assert
 (= c6d075b7f_launchpad_can_recover_tokens c6d075b7f_launchpad_can_recover_tokens))
(assert
 (= c6d075b7f_rewards_lost_on_buy_or_sell c6d075b7f_rewards_lost_on_buy_or_sell))
(assert
 (= c6d075b7f_user_holds_launched_tokens c6d075b7f_user_holds_launched_tokens))
(assert
 (= c6d075b7f_user_pending_rewards c6d075b7f_user_pending_rewards))
(define-fun report_preconditions () Bool (and c6d075b7f_user_holds_launched_tokens
     (< 0 c6d075b7f_user_pending_rewards)
     (not c6d075b7f_launchpad_can_recover_tokens)))
(define-fun report_safety () Bool (=> c6d075b7f_user_holds_launched_tokens
    (= c6d075b7f_distribute_assets_recipient c6d075b7f_intended_recipient)))
(define-fun report_effects () Bool (and c6d075b7f_user_holds_launched_tokens
     (not (= c6d075b7f_distribute_assets_recipient c6d075b7f_intended_recipient))
     c6d075b7f_rewards_lost_on_buy_or_sell
     c6d075b7f_rewards_lost_on_buy_or_sell))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
