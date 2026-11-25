; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca0a90783_captured_balance_at_expiry_minus_one () Int)
(declare-fun ca0a90783_epoch_timestamp_end_n () Int)
(declare-fun ca0a90783_final_epoch_reward_lost () Bool)
(declare-fun ca0a90783_locked_end () Int)
(declare-fun ca0a90783_user_bonded_during_epoch_n () Bool)
(assert
 (= ca0a90783_captured_balance_at_expiry_minus_one ca0a90783_captured_balance_at_expiry_minus_one))
(assert
 (= ca0a90783_epoch_timestamp_end_n ca0a90783_epoch_timestamp_end_n))
(assert
 (= ca0a90783_final_epoch_reward_lost ca0a90783_final_epoch_reward_lost))
(assert
 (= ca0a90783_locked_end ca0a90783_locked_end))
(assert
 (= ca0a90783_user_bonded_during_epoch_n ca0a90783_user_bonded_during_epoch_n))
(define-fun report_preconditions () Bool (and (<= ca0a90783_locked_end ca0a90783_epoch_timestamp_end_n)
     ca0a90783_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> (and (<= ca0a90783_locked_end ca0a90783_epoch_timestamp_end_n)
         ca0a90783_user_bonded_during_epoch_n)
    (< 0 ca0a90783_captured_balance_at_expiry_minus_one)))
(define-fun report_effects () Bool (and (<= ca0a90783_locked_end ca0a90783_epoch_timestamp_end_n)
     ca0a90783_user_bonded_during_epoch_n
     (not (< 0 ca0a90783_captured_balance_at_expiry_minus_one))
     ca0a90783_final_epoch_reward_lost
     ca0a90783_final_epoch_reward_lost))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
