; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun from_address () ReportAddress)
(declare-fun spender_address () ReportAddress)
(declare-fun transferfrom_invoked () Bool)
(declare-fun event_source_address () ReportAddress)
(declare-fun event_emitted () Bool)
(assert
 (= from_address from_address))
(assert
 (= spender_address spender_address))
(assert
 (= transferfrom_invoked transferfrom_invoked))
(assert
 (= event_source_address event_source_address))
(assert
 (= event_emitted event_emitted))
(define-fun report_preconditions () Bool (and (distinct spender_address from_address) transferfrom_invoked))
(define-fun report_safety () Bool (=> (and event_emitted (distinct spender_address from_address))
    (= event_source_address from_address)))
(define-fun report_effects () Bool (and event_emitted
     (distinct spender_address from_address)
     (not (= event_source_address from_address))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
