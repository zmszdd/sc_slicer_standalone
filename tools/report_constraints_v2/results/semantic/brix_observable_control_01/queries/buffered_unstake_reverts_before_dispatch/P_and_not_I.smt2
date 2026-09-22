; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun msg_value () Int)
(declare-fun native_fee () Int)
(declare-fun buffered_flow_used () Bool)
(declare-fun paynative_reverted () Bool)
(declare-fun message_dispatched () Bool)
(assert
 (= msg_value msg_value))
(assert
 (= native_fee native_fee))
(assert
 (= buffered_flow_used buffered_flow_used))
(assert
 (= paynative_reverted paynative_reverted))
(assert
 (= message_dispatched message_dispatched))
(define-fun report_preconditions () Bool (and buffered_flow_used (> msg_value native_fee)))
(define-fun report_safety () Bool (not paynative_reverted))
(define-fun report_effects () Bool (and paynative_reverted (not message_dispatched)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
