; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c66ee3fad_campaign_passed_as_compliant () Bool)
(declare-fun c66ee3fad_chosen_reward_amount () Int)
(declare-fun c66ee3fad_minimum_per_epoch_threshold () Int)
(declare-fun c66ee3fad_post_fee_distributed_amount () Int)
(assert
 (= c66ee3fad_campaign_passed_as_compliant c66ee3fad_campaign_passed_as_compliant))
(assert
 (= c66ee3fad_chosen_reward_amount c66ee3fad_chosen_reward_amount))
(assert
 (= c66ee3fad_minimum_per_epoch_threshold c66ee3fad_minimum_per_epoch_threshold))
(assert
 (= c66ee3fad_post_fee_distributed_amount c66ee3fad_post_fee_distributed_amount))
(define-fun report_preconditions () Bool (> c66ee3fad_chosen_reward_amount c66ee3fad_minimum_per_epoch_threshold))
(define-fun report_safety () Bool (=> (> c66ee3fad_chosen_reward_amount c66ee3fad_minimum_per_epoch_threshold)
    (>= c66ee3fad_post_fee_distributed_amount
        c66ee3fad_minimum_per_epoch_threshold)))
(define-fun report_effects () Bool (and (> c66ee3fad_chosen_reward_amount c66ee3fad_minimum_per_epoch_threshold)
     (not (>= c66ee3fad_post_fee_distributed_amount
              c66ee3fad_minimum_per_epoch_threshold))
     c66ee3fad_campaign_passed_as_compliant))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
