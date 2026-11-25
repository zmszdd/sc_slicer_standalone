; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf1ae9e0e_epoch_timestamp_end_n () Int)
(declare-fun cf1ae9e0e_epoch_total_rewards () Int)
(declare-fun cf1ae9e0e_lock_end () Int)
(declare-fun cf1ae9e0e_natural_expiry_lock_affected () Bool)
(declare-fun cf1ae9e0e_total_bonded_balance () Int)
(declare-fun cf1ae9e0e_user_bonded_balance () Int)
(declare-fun cf1ae9e0e_user_reward_share () Int)
(assert
 (= cf1ae9e0e_epoch_timestamp_end_n cf1ae9e0e_epoch_timestamp_end_n))
(assert
 (= cf1ae9e0e_epoch_total_rewards cf1ae9e0e_epoch_total_rewards))
(assert
 (= cf1ae9e0e_lock_end cf1ae9e0e_lock_end))
(assert
 (= cf1ae9e0e_natural_expiry_lock_affected cf1ae9e0e_natural_expiry_lock_affected))
(assert
 (= cf1ae9e0e_total_bonded_balance cf1ae9e0e_total_bonded_balance))
(assert
 (= cf1ae9e0e_user_bonded_balance cf1ae9e0e_user_bonded_balance))
(assert
 (= cf1ae9e0e_user_reward_share cf1ae9e0e_user_reward_share))
(define-fun report_preconditions () Bool (<= cf1ae9e0e_lock_end cf1ae9e0e_epoch_timestamp_end_n))
(define-fun report_safety () Bool (=> (<= cf1ae9e0e_lock_end cf1ae9e0e_epoch_timestamp_end_n)
    (>= (* cf1ae9e0e_user_reward_share cf1ae9e0e_total_bonded_balance)
        (* cf1ae9e0e_epoch_total_rewards cf1ae9e0e_user_bonded_balance))))
(define-fun report_effects () Bool (and (<= cf1ae9e0e_lock_end cf1ae9e0e_epoch_timestamp_end_n)
     (not (>= (* cf1ae9e0e_user_reward_share cf1ae9e0e_total_bonded_balance)
              (* cf1ae9e0e_epoch_total_rewards cf1ae9e0e_user_bonded_balance)))
     cf1ae9e0e_natural_expiry_lock_affected))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
