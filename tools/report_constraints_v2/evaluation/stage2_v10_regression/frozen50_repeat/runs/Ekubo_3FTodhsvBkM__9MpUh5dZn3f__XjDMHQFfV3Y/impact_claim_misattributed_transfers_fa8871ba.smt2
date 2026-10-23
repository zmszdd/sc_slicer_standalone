; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cff504939_caller () ReportAddress)
(declare-fun cff504939_event_from_address () ReportAddress)
(declare-fun cff504939_token_holder () ReportAddress)
(declare-fun cff504939_transfer_attributed_to_spender () Bool)
(assert
 (= cff504939_caller cff504939_caller))
(assert
 (= cff504939_event_from_address cff504939_event_from_address))
(assert
 (= cff504939_token_holder cff504939_token_holder))
(assert
 (= cff504939_transfer_attributed_to_spender cff504939_transfer_attributed_to_spender))
(define-fun report_preconditions () Bool (distinct cff504939_caller cff504939_token_holder))
(define-fun report_safety () Bool (=> (distinct cff504939_caller cff504939_token_holder)
    (and (= cff504939_event_from_address cff504939_token_holder)
         (not cff504939_transfer_attributed_to_spender))))
(define-fun report_effects () Bool (and (distinct cff504939_caller cff504939_token_holder)
     (not (and (= cff504939_event_from_address cff504939_token_holder)
               (not cff504939_transfer_attributed_to_spender)))))
