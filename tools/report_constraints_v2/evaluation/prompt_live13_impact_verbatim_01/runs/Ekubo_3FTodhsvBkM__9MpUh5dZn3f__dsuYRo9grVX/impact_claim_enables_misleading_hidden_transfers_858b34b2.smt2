; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c81f794a0_event_from_address () ReportAddress)
(declare-fun c81f794a0_misleading_transfer_observable () Bool)
(declare-fun c81f794a0_offchain_reconstructs_from_events () Bool)
(declare-fun c81f794a0_owner_from_parameter () ReportAddress)
(declare-fun c81f794a0_transferfrom_invoked () Bool)
(assert
 (= c81f794a0_event_from_address c81f794a0_event_from_address))
(assert
 (= c81f794a0_misleading_transfer_observable c81f794a0_misleading_transfer_observable))
(assert
 (= c81f794a0_offchain_reconstructs_from_events c81f794a0_offchain_reconstructs_from_events))
(assert
 (= c81f794a0_owner_from_parameter c81f794a0_owner_from_parameter))
(assert
 (= c81f794a0_transferfrom_invoked c81f794a0_transferfrom_invoked))
(define-fun report_preconditions () Bool (and c81f794a0_transferfrom_invoked c81f794a0_offchain_reconstructs_from_events))
(define-fun report_safety () Bool (=> (and c81f794a0_transferfrom_invoked
         c81f794a0_offchain_reconstructs_from_events)
    (or (= c81f794a0_event_from_address c81f794a0_owner_from_parameter)
        (not c81f794a0_misleading_transfer_observable))))
(define-fun report_effects () Bool (and c81f794a0_transferfrom_invoked
     c81f794a0_offchain_reconstructs_from_events
     (not (or (= c81f794a0_event_from_address c81f794a0_owner_from_parameter)
              (not c81f794a0_misleading_transfer_observable)))))
