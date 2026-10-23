; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cda2f2085_event_from_recorded () ReportAddress)
(declare-fun cda2f2085_event_records_spender () Bool)
(declare-fun cda2f2085_from_parameter () ReportAddress)
(declare-fun cda2f2085_transferfrom_invoked () Bool)
(assert
 (= cda2f2085_event_from_recorded cda2f2085_event_from_recorded))
(assert
 (= cda2f2085_event_records_spender cda2f2085_event_records_spender))
(assert
 (= cda2f2085_from_parameter cda2f2085_from_parameter))
(assert
 (= cda2f2085_transferfrom_invoked cda2f2085_transferfrom_invoked))
(define-fun report_preconditions () Bool (and cda2f2085_transferfrom_invoked
     (= cda2f2085_event_from_recorded cda2f2085_from_parameter)))
(define-fun report_safety () Bool (=> cda2f2085_transferfrom_invoked
    (and (= cda2f2085_event_from_recorded cda2f2085_from_parameter)
         (not cda2f2085_event_records_spender))))
(define-fun report_effects () Bool (and cda2f2085_transferfrom_invoked
     (not (and (= cda2f2085_event_from_recorded cda2f2085_from_parameter)
               (not cda2f2085_event_records_spender)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
