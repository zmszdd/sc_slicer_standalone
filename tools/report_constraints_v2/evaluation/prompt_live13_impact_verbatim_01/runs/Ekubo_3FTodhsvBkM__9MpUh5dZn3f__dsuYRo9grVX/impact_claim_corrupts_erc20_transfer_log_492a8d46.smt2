; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c05007057_event_from_address () ReportAddress)
(declare-fun c05007057_from_parameter_address () ReportAddress)
(declare-fun c05007057_offchain_reconstructs_from_events () Bool)
(declare-fun c05007057_transferfrom_invoked () Bool)
(assert
 (= c05007057_event_from_address c05007057_event_from_address))
(assert
 (= c05007057_from_parameter_address c05007057_from_parameter_address))
(assert
 (= c05007057_offchain_reconstructs_from_events c05007057_offchain_reconstructs_from_events))
(assert
 (= c05007057_transferfrom_invoked c05007057_transferfrom_invoked))
(define-fun report_preconditions () Bool (and c05007057_transferfrom_invoked c05007057_offchain_reconstructs_from_events))
(define-fun report_safety () Bool (=> (and c05007057_transferfrom_invoked
         c05007057_offchain_reconstructs_from_events)
    (= c05007057_event_from_address c05007057_from_parameter_address)))
(define-fun report_effects () Bool (and c05007057_transferfrom_invoked
     c05007057_offchain_reconstructs_from_events
     (not (= c05007057_event_from_address c05007057_from_parameter_address))))
