; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9a3276f2_amendment_new_cancel_timestamp () Int)
(declare-fun c9a3276f2_amendment_only_amount_changed () Bool)
(declare-fun c9a3276f2_current_time_before_amend () Int)
(declare-fun c9a3276f2_order_cancel_timestamp_after_amend () Int)
(declare-fun c9a3276f2_order_expired_before_amend () Bool)
(declare-fun c9a3276f2_order_remains_expired_after_amend () Bool)
(assert
 (= c9a3276f2_amendment_new_cancel_timestamp c9a3276f2_amendment_new_cancel_timestamp))
(assert
 (= c9a3276f2_amendment_only_amount_changed c9a3276f2_amendment_only_amount_changed))
(assert
 (= c9a3276f2_current_time_before_amend c9a3276f2_current_time_before_amend))
(assert
 (= c9a3276f2_order_cancel_timestamp_after_amend c9a3276f2_order_cancel_timestamp_after_amend))
(assert
 (= c9a3276f2_order_expired_before_amend c9a3276f2_order_expired_before_amend))
(assert
 (= c9a3276f2_order_remains_expired_after_amend c9a3276f2_order_remains_expired_after_amend))
(define-fun report_preconditions () Bool (and c9a3276f2_order_expired_before_amend
     (> c9a3276f2_amendment_new_cancel_timestamp
        c9a3276f2_current_time_before_amend)
     c9a3276f2_amendment_only_amount_changed))
(define-fun report_safety () Bool (=> c9a3276f2_amendment_only_amount_changed
    (= c9a3276f2_order_cancel_timestamp_after_amend
       c9a3276f2_amendment_new_cancel_timestamp)))
(define-fun report_effects () Bool (and c9a3276f2_amendment_only_amount_changed
     (not (= c9a3276f2_order_cancel_timestamp_after_amend
             c9a3276f2_amendment_new_cancel_timestamp))
     c9a3276f2_order_remains_expired_after_amend))
