; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ceee03a31_emission_distribution_policy_broken () Bool)
(declare-fun ceee03a31_notified_emissions_allocated_to_gauges () Bool)
(declare-fun ceee03a31_total_weight_at_notification () Int)
(assert
 (= ceee03a31_emission_distribution_policy_broken ceee03a31_emission_distribution_policy_broken))
(assert
 (= ceee03a31_notified_emissions_allocated_to_gauges ceee03a31_notified_emissions_allocated_to_gauges))
(assert
 (= ceee03a31_total_weight_at_notification ceee03a31_total_weight_at_notification))
(define-fun report_preconditions () Bool (= 0 ceee03a31_total_weight_at_notification))
(define-fun report_safety () Bool (=> (= 0 ceee03a31_total_weight_at_notification)
    ceee03a31_notified_emissions_allocated_to_gauges))
(define-fun report_effects () Bool (and (= 0 ceee03a31_total_weight_at_notification)
     (not ceee03a31_notified_emissions_allocated_to_gauges)
     ceee03a31_emission_distribution_policy_broken))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
