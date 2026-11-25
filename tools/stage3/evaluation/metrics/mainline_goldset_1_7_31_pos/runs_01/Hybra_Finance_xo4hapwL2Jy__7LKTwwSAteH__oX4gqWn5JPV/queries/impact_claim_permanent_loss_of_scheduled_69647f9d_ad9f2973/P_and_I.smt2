; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c966183b7_notified_emissions_allocated_to_gauges () Bool)
(declare-fun c966183b7_scheduled_emissions_permanently_lost () Bool)
(declare-fun c966183b7_total_weight_at_notification () Int)
(assert
 (= c966183b7_notified_emissions_allocated_to_gauges c966183b7_notified_emissions_allocated_to_gauges))
(assert
 (= c966183b7_scheduled_emissions_permanently_lost c966183b7_scheduled_emissions_permanently_lost))
(assert
 (= c966183b7_total_weight_at_notification c966183b7_total_weight_at_notification))
(define-fun report_preconditions () Bool (= 0 c966183b7_total_weight_at_notification))
(define-fun report_safety () Bool (=> (= 0 c966183b7_total_weight_at_notification)
    c966183b7_notified_emissions_allocated_to_gauges))
(define-fun report_effects () Bool (and (= 0 c966183b7_total_weight_at_notification)
     (not c966183b7_notified_emissions_allocated_to_gauges)
     c966183b7_scheduled_emissions_permanently_lost
     c966183b7_scheduled_emissions_permanently_lost))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
