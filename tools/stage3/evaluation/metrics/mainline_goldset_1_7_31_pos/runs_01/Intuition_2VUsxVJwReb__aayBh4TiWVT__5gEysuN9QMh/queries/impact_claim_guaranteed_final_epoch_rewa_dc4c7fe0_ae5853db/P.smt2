; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce0a86f6d_epoch_timestamp_end_n () Int)
(declare-fun ce0a86f6d_lock_end () Int)
(declare-fun ce0a86f6d_user_bonded_during_epoch_n () Bool)
(declare-fun ce0a86f6d_user_proportional_share_epoch_n () Int)
(declare-fun ce0a86f6d_user_reward_epoch_n () Int)
(declare-fun ce0a86f6d_zero_reward () Int)
(assert
 (= ce0a86f6d_epoch_timestamp_end_n ce0a86f6d_epoch_timestamp_end_n))
(assert
 (= ce0a86f6d_lock_end ce0a86f6d_lock_end))
(assert
 (= ce0a86f6d_user_bonded_during_epoch_n ce0a86f6d_user_bonded_during_epoch_n))
(assert
 (= ce0a86f6d_user_proportional_share_epoch_n ce0a86f6d_user_proportional_share_epoch_n))
(assert
 (= ce0a86f6d_user_reward_epoch_n ce0a86f6d_user_reward_epoch_n))
(assert
 (= ce0a86f6d_zero_reward ce0a86f6d_zero_reward))
(define-fun report_preconditions () Bool (and (<= ce0a86f6d_lock_end ce0a86f6d_epoch_timestamp_end_n)
     ce0a86f6d_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> ce0a86f6d_user_bonded_during_epoch_n
    (= ce0a86f6d_user_reward_epoch_n ce0a86f6d_user_proportional_share_epoch_n)))
(define-fun report_effects () Bool (and ce0a86f6d_user_bonded_during_epoch_n
     (not (= ce0a86f6d_user_reward_epoch_n
             ce0a86f6d_user_proportional_share_epoch_n))
     (= ce0a86f6d_user_reward_epoch_n ce0a86f6d_zero_reward)
     ce0a86f6d_user_bonded_during_epoch_n))
(assert report_preconditions)
(check-sat)
(get-model)
