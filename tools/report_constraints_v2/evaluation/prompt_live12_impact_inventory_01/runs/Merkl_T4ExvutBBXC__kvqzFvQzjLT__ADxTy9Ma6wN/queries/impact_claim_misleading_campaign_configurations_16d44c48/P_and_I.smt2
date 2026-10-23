; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6d2bd058_campaign_created_as_compliant () Bool)
(declare-fun c6d2bd058_chosen_reward_amount () Int)
(declare-fun c6d2bd058_fee_reduced_amount () Int)
(declare-fun c6d2bd058_real_per_epoch_below_minimum () Bool)
(assert
 (= c6d2bd058_campaign_created_as_compliant c6d2bd058_campaign_created_as_compliant))
(assert
 (= c6d2bd058_chosen_reward_amount c6d2bd058_chosen_reward_amount))
(assert
 (= c6d2bd058_fee_reduced_amount c6d2bd058_fee_reduced_amount))
(assert
 (= c6d2bd058_real_per_epoch_below_minimum c6d2bd058_real_per_epoch_below_minimum))
(define-fun report_preconditions () Bool (and (< 0 c6d2bd058_chosen_reward_amount) (< 0 c6d2bd058_fee_reduced_amount)))
(define-fun report_safety () Bool (=> (and (< 0 c6d2bd058_chosen_reward_amount)
         (< 0 c6d2bd058_fee_reduced_amount))
    (or (not c6d2bd058_campaign_created_as_compliant)
        (not c6d2bd058_real_per_epoch_below_minimum))))
(define-fun report_effects () Bool (and (< 0 c6d2bd058_chosen_reward_amount)
     (< 0 c6d2bd058_fee_reduced_amount)
     (not (or (not c6d2bd058_campaign_created_as_compliant)
              (not c6d2bd058_real_per_epoch_below_minimum)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
