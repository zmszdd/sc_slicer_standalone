; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce51706f7_bonded_balance_before_expiry () Int)
(declare-fun ce51706f7_epoch_timestamp_end_n () Int)
(declare-fun ce51706f7_final_epoch_reward_loss_fraction () Int)
(declare-fun ce51706f7_locked_end () Int)
(declare-fun ce51706f7_user_bonded_during_epoch_n () Bool)
(declare-fun ce51706f7_zero_balance () Int)
(assert
 (= ce51706f7_bonded_balance_before_expiry ce51706f7_bonded_balance_before_expiry))
(assert
 (= ce51706f7_epoch_timestamp_end_n ce51706f7_epoch_timestamp_end_n))
(assert
 (= ce51706f7_final_epoch_reward_loss_fraction ce51706f7_final_epoch_reward_loss_fraction))
(assert
 (= ce51706f7_locked_end ce51706f7_locked_end))
(assert
 (= ce51706f7_user_bonded_during_epoch_n ce51706f7_user_bonded_during_epoch_n))
(assert
 (= ce51706f7_zero_balance ce51706f7_zero_balance))
(define-fun report_preconditions () Bool (and (<= ce51706f7_locked_end ce51706f7_epoch_timestamp_end_n)
     ce51706f7_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> (and (<= ce51706f7_locked_end ce51706f7_epoch_timestamp_end_n)
         ce51706f7_user_bonded_during_epoch_n)
    (distinct ce51706f7_bonded_balance_before_expiry ce51706f7_zero_balance)))
(define-fun report_effects () Bool (and (<= ce51706f7_locked_end ce51706f7_epoch_timestamp_end_n)
     ce51706f7_user_bonded_during_epoch_n
     (not (distinct ce51706f7_bonded_balance_before_expiry
                    ce51706f7_zero_balance))
     (= 100 ce51706f7_final_epoch_reward_loss_fraction)
     (= 100 ce51706f7_final_epoch_reward_loss_fraction)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
