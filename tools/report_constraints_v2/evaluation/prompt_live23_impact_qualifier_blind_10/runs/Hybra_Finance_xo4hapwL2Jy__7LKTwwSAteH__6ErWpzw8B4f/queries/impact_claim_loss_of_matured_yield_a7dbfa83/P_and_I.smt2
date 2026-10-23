; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c1d73f8_empty_window_rewards_claimable () Bool)
(declare-fun c4c1d73f8_reward_reserve_positive () Bool)
(declare-fun c4c1d73f8_staked_liquidity_is_zero () Bool)
(declare-fun c4c1d73f8_time_delta_is_nonzero () Bool)
(assert
 (= c4c1d73f8_empty_window_rewards_claimable c4c1d73f8_empty_window_rewards_claimable))
(assert
 (= c4c1d73f8_reward_reserve_positive c4c1d73f8_reward_reserve_positive))
(assert
 (= c4c1d73f8_staked_liquidity_is_zero c4c1d73f8_staked_liquidity_is_zero))
(assert
 (= c4c1d73f8_time_delta_is_nonzero c4c1d73f8_time_delta_is_nonzero))
(define-fun report_preconditions () Bool (and c4c1d73f8_staked_liquidity_is_zero
     c4c1d73f8_time_delta_is_nonzero
     c4c1d73f8_reward_reserve_positive))
(define-fun report_safety () Bool (=> (not c4c1d73f8_empty_window_rewards_claimable)
    (=> (and c4c1d73f8_staked_liquidity_is_zero
             c4c1d73f8_time_delta_is_nonzero
             c4c1d73f8_reward_reserve_positive)
        c4c1d73f8_empty_window_rewards_claimable)))
(define-fun report_effects () Bool (and (not c4c1d73f8_empty_window_rewards_claimable)
     c4c1d73f8_staked_liquidity_is_zero
     c4c1d73f8_time_delta_is_nonzero
     c4c1d73f8_reward_reserve_positive
     (not c4c1d73f8_empty_window_rewards_claimable)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
