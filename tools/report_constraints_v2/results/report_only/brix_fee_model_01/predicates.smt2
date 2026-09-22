; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun exact_fee () Int)
(declare-fun buffered_fee () Int)
(declare-fun msg_value () Int)
(declare-fun message_sent () Bool)
(declare-fun reverted () Bool)
(declare-fun excess_equals () Bool)
(assert
 (= exact_fee exact_fee))
(assert
 (= buffered_fee buffered_fee))
(assert
 (= msg_value msg_value))
(assert
 (= message_sent message_sent))
(assert
 (= reverted reverted))
(assert
 (= excess_equals excess_equals))
(define-fun report_preconditions () Bool (and (= msg_value buffered_fee) (> buffered_fee exact_fee)))
(define-fun report_safety () Bool (=> (and (= msg_value buffered_fee) (> buffered_fee exact_fee))
    (not message_sent)))
(define-fun report_effects () Bool (and (=> (and (= msg_value buffered_fee) (> buffered_fee exact_fee))
         (and reverted (not message_sent)))
     (= reverted (not message_sent))))
