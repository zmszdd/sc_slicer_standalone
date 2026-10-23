; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun c96397b9f_actual_holder_address () ReportAddress)
(declare-fun c96397b9f_caller_is_spender () Bool)
(declare-fun c96397b9f_event_from_address () ReportAddress)
(declare-fun c96397b9f_indexer_attributes_to_spender () Bool)
(assert
 (= c96397b9f_actual_holder_address c96397b9f_actual_holder_address))
(assert
 (= c96397b9f_caller_is_spender c96397b9f_caller_is_spender))
(assert
 (= c96397b9f_event_from_address c96397b9f_event_from_address))
(assert
 (= c96397b9f_indexer_attributes_to_spender c96397b9f_indexer_attributes_to_spender))
(define-fun report_preconditions () Bool c96397b9f_caller_is_spender)
(define-fun report_safety () Bool (=> c96397b9f_caller_is_spender
    (and (= c96397b9f_event_from_address c96397b9f_actual_holder_address)
         (not c96397b9f_indexer_attributes_to_spender))))
(define-fun report_effects () Bool (and c96397b9f_caller_is_spender
     (not (and (= c96397b9f_event_from_address c96397b9f_actual_holder_address)
               (not c96397b9f_indexer_attributes_to_spender)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
