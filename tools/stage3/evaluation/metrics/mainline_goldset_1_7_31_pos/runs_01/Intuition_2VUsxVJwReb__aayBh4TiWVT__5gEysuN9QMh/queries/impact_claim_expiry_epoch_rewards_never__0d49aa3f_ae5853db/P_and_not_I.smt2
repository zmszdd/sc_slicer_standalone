; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c50c7ed8a_epoch_timestamp_end_n () Int)
(declare-fun c50c7ed8a_lock_end () Int)
(declare-fun c50c7ed8a_user_bonded_during_epoch_n () Bool)
(declare-fun c50c7ed8a_user_epoch_n_claimable_rewards () Int)
(declare-fun c50c7ed8a_user_epoch_n_reward_share () Int)
(assert
 (= c50c7ed8a_epoch_timestamp_end_n c50c7ed8a_epoch_timestamp_end_n))
(assert
 (= c50c7ed8a_lock_end c50c7ed8a_lock_end))
(assert
 (= c50c7ed8a_user_bonded_during_epoch_n c50c7ed8a_user_bonded_during_epoch_n))
(assert
 (= c50c7ed8a_user_epoch_n_claimable_rewards c50c7ed8a_user_epoch_n_claimable_rewards))
(assert
 (= c50c7ed8a_user_epoch_n_reward_share c50c7ed8a_user_epoch_n_reward_share))
(define-fun report_preconditions () Bool (and (<= c50c7ed8a_lock_end c50c7ed8a_epoch_timestamp_end_n)
     c50c7ed8a_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> c50c7ed8a_user_bonded_during_epoch_n
    (>= c50c7ed8a_user_epoch_n_claimable_rewards
        c50c7ed8a_user_epoch_n_reward_share)))
(define-fun report_effects () Bool (and c50c7ed8a_user_bonded_during_epoch_n
     (not (>= c50c7ed8a_user_epoch_n_claimable_rewards
              c50c7ed8a_user_epoch_n_reward_share))
     (= 0 c50c7ed8a_user_epoch_n_claimable_rewards)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
