; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7bcf17b1_epoch_timestamp_end_n () Int)
(declare-fun c7bcf17b1_lock_end () Int)
(declare-fun c7bcf17b1_user_bonded_during_epoch_n () Bool)
(declare-fun c7bcf17b1_user_proportional_share_epoch_n () Int)
(declare-fun c7bcf17b1_user_received_rewards_epoch_n () Int)
(assert
 (= c7bcf17b1_epoch_timestamp_end_n c7bcf17b1_epoch_timestamp_end_n))
(assert
 (= c7bcf17b1_lock_end c7bcf17b1_lock_end))
(assert
 (= c7bcf17b1_user_bonded_during_epoch_n c7bcf17b1_user_bonded_during_epoch_n))
(assert
 (= c7bcf17b1_user_proportional_share_epoch_n c7bcf17b1_user_proportional_share_epoch_n))
(assert
 (= c7bcf17b1_user_received_rewards_epoch_n c7bcf17b1_user_received_rewards_epoch_n))
(define-fun report_preconditions () Bool (and (<= c7bcf17b1_lock_end c7bcf17b1_epoch_timestamp_end_n)
     c7bcf17b1_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> c7bcf17b1_user_bonded_during_epoch_n
    (>= c7bcf17b1_user_received_rewards_epoch_n
        c7bcf17b1_user_proportional_share_epoch_n)))
(define-fun report_effects () Bool (and c7bcf17b1_user_bonded_during_epoch_n
     (not (>= c7bcf17b1_user_received_rewards_epoch_n
              c7bcf17b1_user_proportional_share_epoch_n))
     (= 0 c7bcf17b1_user_received_rewards_epoch_n)
     c7bcf17b1_user_bonded_during_epoch_n))
(assert report_preconditions)
(check-sat)
(get-model)
