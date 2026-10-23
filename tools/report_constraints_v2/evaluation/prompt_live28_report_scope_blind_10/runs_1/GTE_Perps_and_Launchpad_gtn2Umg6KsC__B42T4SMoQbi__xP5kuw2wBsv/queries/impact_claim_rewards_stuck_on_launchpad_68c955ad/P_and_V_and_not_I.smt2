; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdcd52f92_pending_quote_rewards_before () Int)
(declare-fun cdcd52f92_rewards_forwarded_to_user () Bool)
(declare-fun cdcd52f92_rewards_stuck_on_launchpad_observed () Bool)
(declare-fun cdcd52f92_stake_shares_before () Int)
(assert
 (= cdcd52f92_pending_quote_rewards_before cdcd52f92_pending_quote_rewards_before))
(assert
 (= cdcd52f92_rewards_forwarded_to_user cdcd52f92_rewards_forwarded_to_user))
(assert
 (= cdcd52f92_rewards_stuck_on_launchpad_observed cdcd52f92_rewards_stuck_on_launchpad_observed))
(assert
 (= cdcd52f92_stake_shares_before cdcd52f92_stake_shares_before))
(define-fun report_preconditions () Bool (and (< 0 cdcd52f92_stake_shares_before)
     (< 0 cdcd52f92_pending_quote_rewards_before)))
(define-fun report_safety () Bool (=> cdcd52f92_rewards_stuck_on_launchpad_observed
    (=> (and (< 0 cdcd52f92_stake_shares_before)
             (< 0 cdcd52f92_pending_quote_rewards_before))
        cdcd52f92_rewards_forwarded_to_user)))
(define-fun report_effects () Bool (and cdcd52f92_rewards_stuck_on_launchpad_observed
     (< 0 cdcd52f92_stake_shares_before)
     (< 0 cdcd52f92_pending_quote_rewards_before)
     (not cdcd52f92_rewards_forwarded_to_user)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
