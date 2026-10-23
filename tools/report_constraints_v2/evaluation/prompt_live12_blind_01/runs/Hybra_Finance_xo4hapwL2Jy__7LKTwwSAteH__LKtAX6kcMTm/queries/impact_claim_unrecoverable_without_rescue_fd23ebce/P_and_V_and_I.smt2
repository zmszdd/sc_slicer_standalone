; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce91ba209_pool_live_weight_is_zero () Bool)
(declare-fun ce91ba209_rewards_transferred () Bool)
(declare-fun ce91ba209_stuck_emissions_recoverable_without_rescue () Bool)
(declare-fun ce91ba209_total_weight_is_zero () Bool)
(assert
 (= ce91ba209_pool_live_weight_is_zero ce91ba209_pool_live_weight_is_zero))
(assert
 (= ce91ba209_rewards_transferred ce91ba209_rewards_transferred))
(assert
 (= ce91ba209_stuck_emissions_recoverable_without_rescue ce91ba209_stuck_emissions_recoverable_without_rescue))
(assert
 (= ce91ba209_total_weight_is_zero ce91ba209_total_weight_is_zero))
(define-fun report_preconditions () Bool (and ce91ba209_total_weight_is_zero ce91ba209_pool_live_weight_is_zero))
(define-fun report_safety () Bool (=> (and ce91ba209_total_weight_is_zero
         ce91ba209_pool_live_weight_is_zero
         ce91ba209_rewards_transferred)
    ce91ba209_stuck_emissions_recoverable_without_rescue))
(define-fun report_effects () Bool (and ce91ba209_total_weight_is_zero
     ce91ba209_pool_live_weight_is_zero
     ce91ba209_rewards_transferred
     (not ce91ba209_stuck_emissions_recoverable_without_rescue)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
