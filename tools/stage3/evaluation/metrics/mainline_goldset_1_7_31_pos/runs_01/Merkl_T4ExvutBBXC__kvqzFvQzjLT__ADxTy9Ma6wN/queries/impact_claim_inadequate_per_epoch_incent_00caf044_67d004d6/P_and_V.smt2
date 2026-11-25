; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c95641cf5_chosen_reward_amount () Int)
(declare-fun c95641cf5_inadequate_incentives_observed () Bool)
(declare-fun c95641cf5_minimum_per_epoch_threshold () Int)
(declare-fun c95641cf5_post_fee_distributed_amount () Int)
(assert
 (= c95641cf5_chosen_reward_amount c95641cf5_chosen_reward_amount))
(assert
 (= c95641cf5_inadequate_incentives_observed c95641cf5_inadequate_incentives_observed))
(assert
 (= c95641cf5_minimum_per_epoch_threshold c95641cf5_minimum_per_epoch_threshold))
(assert
 (= c95641cf5_post_fee_distributed_amount c95641cf5_post_fee_distributed_amount))
(define-fun report_preconditions () Bool (and (> c95641cf5_chosen_reward_amount c95641cf5_minimum_per_epoch_threshold)
     c95641cf5_inadequate_incentives_observed))
(define-fun report_safety () Bool (>= c95641cf5_post_fee_distributed_amount c95641cf5_minimum_per_epoch_threshold))
(define-fun report_effects () Bool (and c95641cf5_inadequate_incentives_observed
     (not (>= c95641cf5_post_fee_distributed_amount
              c95641cf5_minimum_per_epoch_threshold))
     c95641cf5_inadequate_incentives_observed
     (< c95641cf5_post_fee_distributed_amount
        c95641cf5_minimum_per_epoch_threshold)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
