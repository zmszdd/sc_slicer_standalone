; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun user_earned_rewards () Int)
(declare-fun token_graduated () Bool)
(declare-fun user_transfers_tokens () Bool)
(declare-fun reward_recipient () ReportAddress)
(declare-fun user_address () ReportAddress)
(declare-fun launchpad_address () ReportAddress)
(assert
 (= user_earned_rewards user_earned_rewards))
(assert
 (= token_graduated token_graduated))
(assert
 (= user_transfers_tokens user_transfers_tokens))
(assert
 (= reward_recipient reward_recipient))
(assert
 (= user_address user_address))
(assert
 (= launchpad_address launchpad_address))
(define-fun report_preconditions () Bool (and (< 0 user_earned_rewards) token_graduated user_transfers_tokens))
(define-fun report_safety () Bool (=> (and token_graduated user_transfers_tokens (< 0 user_earned_rewards))
    (= reward_recipient user_address)))
(define-fun report_effects () Bool (and token_graduated
     user_transfers_tokens
     (< 0 user_earned_rewards)
     (not (= reward_recipient user_address))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
