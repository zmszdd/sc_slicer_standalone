; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c31b23d39_captured_bonded_balance () Int)
(declare-fun c31b23d39_epoch_n_rewards_claimable () Bool)
(declare-fun c31b23d39_epoch_timestamp_end_n () Int)
(declare-fun c31b23d39_lock_end () Int)
(declare-fun c31b23d39_user_bonded_during_epoch_n () Bool)
(declare-fun c31b23d39_zero_balance () Int)
(assert
 (= c31b23d39_captured_bonded_balance c31b23d39_captured_bonded_balance))
(assert
 (= c31b23d39_epoch_n_rewards_claimable c31b23d39_epoch_n_rewards_claimable))
(assert
 (= c31b23d39_epoch_timestamp_end_n c31b23d39_epoch_timestamp_end_n))
(assert
 (= c31b23d39_lock_end c31b23d39_lock_end))
(assert
 (= c31b23d39_user_bonded_during_epoch_n c31b23d39_user_bonded_during_epoch_n))
(assert
 (= c31b23d39_zero_balance c31b23d39_zero_balance))
(define-fun report_preconditions () Bool (and (<= c31b23d39_lock_end c31b23d39_epoch_timestamp_end_n)
     c31b23d39_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> (and (<= c31b23d39_lock_end c31b23d39_epoch_timestamp_end_n)
         c31b23d39_user_bonded_during_epoch_n)
    (distinct c31b23d39_captured_bonded_balance c31b23d39_zero_balance)))
(define-fun report_effects () Bool (and (<= c31b23d39_lock_end c31b23d39_epoch_timestamp_end_n)
     c31b23d39_user_bonded_during_epoch_n
     (not (distinct c31b23d39_captured_bonded_balance c31b23d39_zero_balance))
     (not c31b23d39_epoch_n_rewards_claimable)))
