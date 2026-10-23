; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cd9dc09dd_caller () ReportAddress)
(declare-fun cd9dc09dd_event_from () ReportAddress)
(declare-fun cd9dc09dd_token_holder () ReportAddress)
(declare-fun cd9dc09dd_wallet_history_misleading () Bool)
(assert
 (= cd9dc09dd_caller cd9dc09dd_caller))
(assert
 (= cd9dc09dd_event_from cd9dc09dd_event_from))
(assert
 (= cd9dc09dd_token_holder cd9dc09dd_token_holder))
(assert
 (= cd9dc09dd_wallet_history_misleading cd9dc09dd_wallet_history_misleading))
(define-fun report_preconditions () Bool (distinct cd9dc09dd_caller cd9dc09dd_token_holder))
(define-fun report_safety () Bool (=> (distinct cd9dc09dd_caller cd9dc09dd_token_holder)
    (and (= cd9dc09dd_event_from cd9dc09dd_token_holder)
         (not cd9dc09dd_wallet_history_misleading))))
(define-fun report_effects () Bool (and (distinct cd9dc09dd_caller cd9dc09dd_token_holder)
     (not (and (= cd9dc09dd_event_from cd9dc09dd_token_holder)
               (not cd9dc09dd_wallet_history_misleading)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
