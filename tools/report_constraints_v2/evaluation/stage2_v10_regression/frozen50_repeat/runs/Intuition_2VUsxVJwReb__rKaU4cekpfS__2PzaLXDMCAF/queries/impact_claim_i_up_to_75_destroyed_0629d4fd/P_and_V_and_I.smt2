; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca318174e_destroyed_yield () Int)
(declare-fun ca318174e_destroyed_yield_upper_bound () Int)
(declare-fun ca318174e_first_claim_attempted () Bool)
(declare-fun ca318174e_first_epoch_matured_yield () Int)
(declare-fun ca318174e_passive_staker_no_multivault () Bool)
(declare-fun ca318174e_prior_epoch_eligible_rewards () Int)
(declare-fun ca318174e_raw_utilization_delta () Int)
(assert
 (= ca318174e_destroyed_yield ca318174e_destroyed_yield))
(assert
 (= ca318174e_destroyed_yield_upper_bound ca318174e_destroyed_yield_upper_bound))
(assert
 (= ca318174e_first_claim_attempted ca318174e_first_claim_attempted))
(assert
 (= ca318174e_first_epoch_matured_yield ca318174e_first_epoch_matured_yield))
(assert
 (= ca318174e_passive_staker_no_multivault ca318174e_passive_staker_no_multivault))
(assert
 (= ca318174e_prior_epoch_eligible_rewards ca318174e_prior_epoch_eligible_rewards))
(assert
 (= ca318174e_raw_utilization_delta ca318174e_raw_utilization_delta))
(define-fun report_preconditions () Bool (and ca318174e_passive_staker_no_multivault
     ca318174e_first_claim_attempted
     (= 0 ca318174e_raw_utilization_delta)
     (= 0 ca318174e_prior_epoch_eligible_rewards)))
(define-fun report_safety () Bool (=> (= ca318174e_destroyed_yield_upper_bound
       (* ca318174e_first_epoch_matured_yield 75))
    (=> (and ca318174e_passive_staker_no_multivault
             ca318174e_first_claim_attempted
             (= 0 ca318174e_raw_utilization_delta)
             (= 0 ca318174e_prior_epoch_eligible_rewards))
        (= 0 ca318174e_destroyed_yield))))
(define-fun report_effects () Bool (and (= ca318174e_destroyed_yield_upper_bound
        (* ca318174e_first_epoch_matured_yield 75))
     ca318174e_passive_staker_no_multivault
     ca318174e_first_claim_attempted
     (= 0 ca318174e_raw_utilization_delta)
     (= 0 ca318174e_prior_epoch_eligible_rewards)
     (not (= 0 ca318174e_destroyed_yield))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
