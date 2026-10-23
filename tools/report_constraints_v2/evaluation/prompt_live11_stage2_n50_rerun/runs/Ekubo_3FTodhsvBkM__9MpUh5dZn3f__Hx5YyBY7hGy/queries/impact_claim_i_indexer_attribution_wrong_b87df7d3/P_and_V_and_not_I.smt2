; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c9a62a4ae_actual_holder_address () ReportAddress)
(declare-fun c9a62a4ae_event_from_address () ReportAddress)
(declare-fun c9a62a4ae_from_is_debited_holder () Bool)
(declare-fun c9a62a4ae_indexer_attribution_correct () Bool)
(declare-fun c9a62a4ae_transfer_from_invoked () Bool)
(assert
 (= c9a62a4ae_actual_holder_address c9a62a4ae_actual_holder_address))
(assert
 (= c9a62a4ae_event_from_address c9a62a4ae_event_from_address))
(assert
 (= c9a62a4ae_from_is_debited_holder c9a62a4ae_from_is_debited_holder))
(assert
 (= c9a62a4ae_indexer_attribution_correct c9a62a4ae_indexer_attribution_correct))
(assert
 (= c9a62a4ae_transfer_from_invoked c9a62a4ae_transfer_from_invoked))
(define-fun report_preconditions () Bool (and c9a62a4ae_transfer_from_invoked c9a62a4ae_from_is_debited_holder))
(define-fun report_safety () Bool (=> (and c9a62a4ae_transfer_from_invoked c9a62a4ae_from_is_debited_holder)
    (and (= c9a62a4ae_event_from_address c9a62a4ae_actual_holder_address)
         c9a62a4ae_indexer_attribution_correct)))
(define-fun report_effects () Bool (and c9a62a4ae_transfer_from_invoked
     c9a62a4ae_from_is_debited_holder
     (not (and (= c9a62a4ae_event_from_address c9a62a4ae_actual_holder_address)
               c9a62a4ae_indexer_attribution_correct))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
