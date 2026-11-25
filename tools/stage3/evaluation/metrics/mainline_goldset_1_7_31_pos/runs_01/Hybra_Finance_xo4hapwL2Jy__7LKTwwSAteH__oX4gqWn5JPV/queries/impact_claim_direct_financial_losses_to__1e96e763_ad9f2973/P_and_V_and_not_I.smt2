; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7717ea09_notified_emissions_allocated_to_gauges () Bool)
(declare-fun c7717ea09_stakeholders_suffer_direct_financial_loss () Bool)
(declare-fun c7717ea09_total_weight () Int)
(assert
 (= c7717ea09_notified_emissions_allocated_to_gauges c7717ea09_notified_emissions_allocated_to_gauges))
(assert
 (= c7717ea09_stakeholders_suffer_direct_financial_loss c7717ea09_stakeholders_suffer_direct_financial_loss))
(assert
 (= c7717ea09_total_weight c7717ea09_total_weight))
(define-fun report_preconditions () Bool (= 0 c7717ea09_total_weight))
(define-fun report_safety () Bool (=> (= 0 c7717ea09_total_weight)
    c7717ea09_notified_emissions_allocated_to_gauges))
(define-fun report_effects () Bool (and (= 0 c7717ea09_total_weight)
     (not c7717ea09_notified_emissions_allocated_to_gauges)
     c7717ea09_stakeholders_suffer_direct_financial_loss))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
