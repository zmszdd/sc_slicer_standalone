; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun token_topic_address () ReportAddress)
(declare-fun recipient_topic_address () ReportAddress)
(declare-fun stored_token_address () ReportAddress)
(declare-fun stored_recipient_address () ReportAddress)
(assert
 (= token_topic_address token_topic_address))
(assert
 (= recipient_topic_address recipient_topic_address))
(assert
 (= stored_token_address stored_token_address))
(assert
 (= stored_recipient_address stored_recipient_address))
(define-fun report_preconditions () Bool (and (distinct stored_token_address stored_recipient_address)
     (distinct token_topic_address recipient_topic_address)))
(define-fun report_safety () Bool (=> (and (distinct stored_token_address stored_recipient_address)
         (distinct token_topic_address recipient_topic_address))
    (and (= token_topic_address stored_token_address)
         (= recipient_topic_address stored_recipient_address))))
(define-fun report_effects () Bool (and (distinct stored_token_address stored_recipient_address)
     (distinct token_topic_address recipient_topic_address)
     (not (and (= token_topic_address stored_token_address)
               (= recipient_topic_address stored_recipient_address)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
