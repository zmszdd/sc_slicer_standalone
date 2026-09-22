; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun stored_token () ReportAddress)
(declare-fun stored_recipient () ReportAddress)
(declare-fun declared_token_position () ReportAddress)
(declare-fun declared_recipient_position () ReportAddress)
(declare-fun indexed_token_topic_value () ReportAddress)
(declare-fun indexed_recipient_topic_value () ReportAddress)
(assert
 (= stored_token stored_token))
(assert
 (= stored_recipient stored_recipient))
(assert
 (= declared_token_position declared_token_position))
(assert
 (= declared_recipient_position declared_recipient_position))
(assert
 (= indexed_token_topic_value indexed_token_topic_value))
(assert
 (= indexed_recipient_topic_value indexed_recipient_topic_value))
(define-fun report_preconditions () Bool (and (= stored_recipient stored_recipient)
     (= declared_token_position stored_token)))
(define-fun report_safety () Bool (=> (and (= stored_token stored_token) (= stored_recipient stored_recipient))
    (and (= indexed_token_topic_value stored_token)
         (= indexed_recipient_topic_value stored_recipient))))
(define-fun report_effects () Bool (and (= stored_token stored_token)
     (= stored_recipient stored_recipient)
     (not (and (= indexed_token_topic_value stored_token)
               (= indexed_recipient_topic_value stored_recipient)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
