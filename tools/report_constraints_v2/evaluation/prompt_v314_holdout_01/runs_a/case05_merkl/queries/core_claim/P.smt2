; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun event_token_position_value () ReportAddress)
(declare-fun event_recipient_position_value () ReportAddress)
(declare-fun onchain_token () ReportAddress)
(declare-fun onchain_recipient () ReportAddress)
(declare-fun offchain_consumers_rely_on_topics () Bool)
(assert
 (= event_token_position_value event_token_position_value))
(assert
 (= event_recipient_position_value event_recipient_position_value))
(assert
 (= onchain_token onchain_token))
(assert
 (= onchain_recipient onchain_recipient))
(assert
 (= offchain_consumers_rely_on_topics offchain_consumers_rely_on_topics))
(define-fun report_preconditions () Bool (and (distinct onchain_token onchain_recipient)
     (distinct event_token_position_value event_recipient_position_value)
     offchain_consumers_rely_on_topics))
(define-fun report_safety () Bool (=> (and (distinct onchain_token onchain_recipient)
         (distinct event_token_position_value event_recipient_position_value)
         offchain_consumers_rely_on_topics)
    (not (or (= event_token_position_value onchain_recipient)
             (= event_recipient_position_value onchain_token)))))
(define-fun report_effects () Bool (and (distinct onchain_token onchain_recipient)
     (distinct event_token_position_value event_recipient_position_value)
     offchain_consumers_rely_on_topics
     (or (= event_token_position_value onchain_recipient)
         (= event_recipient_position_value onchain_token))))
(assert report_preconditions)
(check-sat)
(get-model)
