; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfd98e47f_bonded_during_epoch_n () Bool)
(declare-fun cfd98e47f_captured_balance_at_expiry_minus_one () Int)
(declare-fun cfd98e47f_epoch_timestamp_end_n () Int)
(declare-fun cfd98e47f_lock_duration_le_epoch_length () Bool)
(declare-fun cfd98e47f_lock_end () Int)
(declare-fun cfd98e47f_total_reward_loss_occurred () Bool)
(declare-fun cfd98e47f_zero_balance () Int)
(assert
 (= cfd98e47f_bonded_during_epoch_n cfd98e47f_bonded_during_epoch_n))
(assert
 (= cfd98e47f_captured_balance_at_expiry_minus_one cfd98e47f_captured_balance_at_expiry_minus_one))
(assert
 (= cfd98e47f_epoch_timestamp_end_n cfd98e47f_epoch_timestamp_end_n))
(assert
 (= cfd98e47f_lock_duration_le_epoch_length cfd98e47f_lock_duration_le_epoch_length))
(assert
 (= cfd98e47f_lock_end cfd98e47f_lock_end))
(assert
 (= cfd98e47f_total_reward_loss_occurred cfd98e47f_total_reward_loss_occurred))
(assert
 (= cfd98e47f_zero_balance cfd98e47f_zero_balance))
(define-fun report_preconditions () Bool (and (<= cfd98e47f_lock_end cfd98e47f_epoch_timestamp_end_n)
     cfd98e47f_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> (and (<= cfd98e47f_lock_end cfd98e47f_epoch_timestamp_end_n)
         cfd98e47f_bonded_during_epoch_n)
    (distinct cfd98e47f_captured_balance_at_expiry_minus_one
              cfd98e47f_zero_balance)))
(define-fun report_effects () Bool (and (<= cfd98e47f_lock_end cfd98e47f_epoch_timestamp_end_n)
     cfd98e47f_bonded_during_epoch_n
     (not (distinct cfd98e47f_captured_balance_at_expiry_minus_one
                    cfd98e47f_zero_balance))
     cfd98e47f_lock_duration_le_epoch_length
     cfd98e47f_total_reward_loss_occurred
     cfd98e47f_lock_duration_le_epoch_length))
(assert report_preconditions)
(check-sat)
(get-model)
