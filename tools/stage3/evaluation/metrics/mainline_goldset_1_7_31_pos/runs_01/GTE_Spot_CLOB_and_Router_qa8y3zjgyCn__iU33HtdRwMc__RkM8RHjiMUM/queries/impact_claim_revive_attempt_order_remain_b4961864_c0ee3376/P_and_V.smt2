; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8232b70b_amendment_cancel_timestamp () Int)
(declare-fun c8232b70b_amendment_only_amount_in_base () Bool)
(declare-fun c8232b70b_current_time_at_amend () Int)
(declare-fun c8232b70b_order_cancel_timestamp_after_amend () Int)
(declare-fun c8232b70b_order_expired_before_amend () Bool)
(declare-fun c8232b70b_order_remains_expired_after_amend () Bool)
(assert
 (= c8232b70b_amendment_cancel_timestamp c8232b70b_amendment_cancel_timestamp))
(assert
 (= c8232b70b_amendment_only_amount_in_base c8232b70b_amendment_only_amount_in_base))
(assert
 (= c8232b70b_current_time_at_amend c8232b70b_current_time_at_amend))
(assert
 (= c8232b70b_order_cancel_timestamp_after_amend c8232b70b_order_cancel_timestamp_after_amend))
(assert
 (= c8232b70b_order_expired_before_amend c8232b70b_order_expired_before_amend))
(assert
 (= c8232b70b_order_remains_expired_after_amend c8232b70b_order_remains_expired_after_amend))
(define-fun report_preconditions () Bool (and c8232b70b_order_expired_before_amend
     (> c8232b70b_amendment_cancel_timestamp c8232b70b_current_time_at_amend)
     c8232b70b_amendment_only_amount_in_base))
(define-fun report_safety () Bool (=> (and c8232b70b_order_expired_before_amend
         (> c8232b70b_amendment_cancel_timestamp
            c8232b70b_current_time_at_amend)
         c8232b70b_amendment_only_amount_in_base)
    (= c8232b70b_order_cancel_timestamp_after_amend
       c8232b70b_amendment_cancel_timestamp)))
(define-fun report_effects () Bool (and c8232b70b_order_expired_before_amend
     (> c8232b70b_amendment_cancel_timestamp c8232b70b_current_time_at_amend)
     c8232b70b_amendment_only_amount_in_base
     (not (= c8232b70b_order_cancel_timestamp_after_amend
             c8232b70b_amendment_cancel_timestamp))
     c8232b70b_order_remains_expired_after_amend))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
