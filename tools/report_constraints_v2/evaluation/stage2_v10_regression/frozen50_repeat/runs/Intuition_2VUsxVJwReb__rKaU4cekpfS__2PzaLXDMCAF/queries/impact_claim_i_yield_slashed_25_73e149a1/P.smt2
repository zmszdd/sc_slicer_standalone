; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c926c5237_basis_points_divisor () Int)
(declare-fun c926c5237_first_claim_attempted () Bool)
(declare-fun c926c5237_first_claim_yield_ratio () Int)
(declare-fun c926c5237_passive_stake_no_multivault () Bool)
(declare-fun c926c5237_prior_epoch_eligible_rewards () Int)
(declare-fun c926c5237_raw_utilization_delta () Int)
(assert
 (= c926c5237_basis_points_divisor c926c5237_basis_points_divisor))
(assert
 (= c926c5237_first_claim_attempted c926c5237_first_claim_attempted))
(assert
 (= c926c5237_first_claim_yield_ratio c926c5237_first_claim_yield_ratio))
(assert
 (= c926c5237_passive_stake_no_multivault c926c5237_passive_stake_no_multivault))
(assert
 (= c926c5237_prior_epoch_eligible_rewards c926c5237_prior_epoch_eligible_rewards))
(assert
 (= c926c5237_raw_utilization_delta c926c5237_raw_utilization_delta))
(define-fun report_preconditions () Bool (and c926c5237_passive_stake_no_multivault
     c926c5237_first_claim_attempted
     (= 0 c926c5237_raw_utilization_delta)
     (= 0 c926c5237_prior_epoch_eligible_rewards)))
(define-fun report_safety () Bool (=> (and c926c5237_passive_stake_no_multivault
         c926c5237_first_claim_attempted
         (= 0 c926c5237_prior_epoch_eligible_rewards))
    (= c926c5237_first_claim_yield_ratio c926c5237_basis_points_divisor)))
(define-fun report_effects () Bool (and c926c5237_passive_stake_no_multivault
     c926c5237_first_claim_attempted
     (= 0 c926c5237_prior_epoch_eligible_rewards)
     (not (= c926c5237_first_claim_yield_ratio c926c5237_basis_points_divisor))))
(assert report_preconditions)
(check-sat)
(get-model)
