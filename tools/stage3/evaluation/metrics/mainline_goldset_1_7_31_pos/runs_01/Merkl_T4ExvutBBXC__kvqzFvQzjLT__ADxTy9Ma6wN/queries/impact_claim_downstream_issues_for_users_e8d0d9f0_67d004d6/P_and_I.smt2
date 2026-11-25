; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd2c9f48f_actual_payout_below_minimum () Bool)
(declare-fun cd2c9f48f_chosen_reward_amount () Int)
(declare-fun cd2c9f48f_min_per_epoch_threshold () Int)
(declare-fun cd2c9f48f_post_fee_distributed_amount () Int)
(assert
 (= cd2c9f48f_actual_payout_below_minimum cd2c9f48f_actual_payout_below_minimum))
(assert
 (= cd2c9f48f_chosen_reward_amount cd2c9f48f_chosen_reward_amount))
(assert
 (= cd2c9f48f_min_per_epoch_threshold cd2c9f48f_min_per_epoch_threshold))
(assert
 (= cd2c9f48f_post_fee_distributed_amount cd2c9f48f_post_fee_distributed_amount))
(define-fun report_preconditions () Bool (> cd2c9f48f_chosen_reward_amount cd2c9f48f_min_per_epoch_threshold))
(define-fun report_safety () Bool (=> (> cd2c9f48f_chosen_reward_amount cd2c9f48f_min_per_epoch_threshold)
    (>= cd2c9f48f_post_fee_distributed_amount cd2c9f48f_min_per_epoch_threshold)))
(define-fun report_effects () Bool (and (> cd2c9f48f_chosen_reward_amount cd2c9f48f_min_per_epoch_threshold)
     (not (>= cd2c9f48f_post_fee_distributed_amount
              cd2c9f48f_min_per_epoch_threshold))
     cd2c9f48f_actual_payout_below_minimum))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
