; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c30438a42_captured_balance_at_expiry_minus_one () Int)
(declare-fun c30438a42_epoch_timestamp_end_n () Int)
(declare-fun c30438a42_full_reward_percent () Int)
(declare-fun c30438a42_lock_end () Int)
(declare-fun c30438a42_rewards_lost_fraction () Int)
(declare-fun c30438a42_user_bonded_in_epoch_n () Bool)
(declare-fun c30438a42_zero_balance () Int)
(assert
 (= c30438a42_captured_balance_at_expiry_minus_one c30438a42_captured_balance_at_expiry_minus_one))
(assert
 (= c30438a42_epoch_timestamp_end_n c30438a42_epoch_timestamp_end_n))
(assert
 (= c30438a42_full_reward_percent c30438a42_full_reward_percent))
(assert
 (= c30438a42_lock_end c30438a42_lock_end))
(assert
 (= c30438a42_rewards_lost_fraction c30438a42_rewards_lost_fraction))
(assert
 (= c30438a42_user_bonded_in_epoch_n c30438a42_user_bonded_in_epoch_n))
(assert
 (= c30438a42_zero_balance c30438a42_zero_balance))
(define-fun report_preconditions () Bool (and (<= c30438a42_lock_end c30438a42_epoch_timestamp_end_n)
     c30438a42_user_bonded_in_epoch_n))
(define-fun report_safety () Bool (=> (and (<= c30438a42_lock_end c30438a42_epoch_timestamp_end_n)
         c30438a42_user_bonded_in_epoch_n)
    (> c30438a42_captured_balance_at_expiry_minus_one c30438a42_zero_balance)))
(define-fun report_effects () Bool (and (<= c30438a42_lock_end c30438a42_epoch_timestamp_end_n)
     c30438a42_user_bonded_in_epoch_n
     (not (> c30438a42_captured_balance_at_expiry_minus_one
             c30438a42_zero_balance))
     (= c30438a42_rewards_lost_fraction c30438a42_full_reward_percent)
     (= c30438a42_rewards_lost_fraction c30438a42_full_reward_percent)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
