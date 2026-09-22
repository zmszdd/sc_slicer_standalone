; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun msg_value () Int)
(declare-fun exact_native_fee () Int)
(declare-fun buffered_fee () Int)
(declare-fun unstake_reverted_not_enough_native () Bool)
(assert
 (= msg_value msg_value))
(assert
 (= exact_native_fee exact_native_fee))
(assert
 (= buffered_fee buffered_fee))
(assert
 (= unstake_reverted_not_enough_native unstake_reverted_not_enough_native))
(define-fun report_preconditions () Bool (and (> msg_value exact_native_fee)
     (> buffered_fee exact_native_fee)
     (> msg_value exact_native_fee)))
(define-fun report_safety () Bool (=> (= buffered_fee (* exact_native_fee 110))
    (=> (>= msg_value exact_native_fee)
        (not unstake_reverted_not_enough_native))))
(define-fun report_effects () Bool (and (= buffered_fee (* exact_native_fee 110))
     (>= msg_value exact_native_fee)
     (not (not unstake_reverted_not_enough_native))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
