; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdbb03139_next_call_is_swap_occurred () Bool)
(declare-fun cdbb03139_swap_amount_in_includes_accrued_fee () Bool)
(declare-fun cdbb03139_time_elapsed_at_fee_accrual () Int)
(declare-fun cdbb03139_time_elapsed_before_next_swap () Int)
(assert
 (= cdbb03139_next_call_is_swap_occurred cdbb03139_next_call_is_swap_occurred))
(assert
 (= cdbb03139_swap_amount_in_includes_accrued_fee cdbb03139_swap_amount_in_includes_accrued_fee))
(assert
 (= cdbb03139_time_elapsed_at_fee_accrual cdbb03139_time_elapsed_at_fee_accrual))
(assert
 (= cdbb03139_time_elapsed_before_next_swap cdbb03139_time_elapsed_before_next_swap))
(define-fun report_preconditions () Bool (and (= 0 cdbb03139_time_elapsed_before_next_swap)
     (= 0 cdbb03139_time_elapsed_at_fee_accrual)
     cdbb03139_next_call_is_swap_occurred))
(define-fun report_safety () Bool (=> cdbb03139_swap_amount_in_includes_accrued_fee
    (=> (and (= 0 cdbb03139_time_elapsed_before_next_swap)
             (= 0 cdbb03139_time_elapsed_at_fee_accrual)
             cdbb03139_next_call_is_swap_occurred)
        (not cdbb03139_swap_amount_in_includes_accrued_fee))))
(define-fun report_effects () Bool (and cdbb03139_swap_amount_in_includes_accrued_fee
     (= 0 cdbb03139_time_elapsed_before_next_swap)
     (= 0 cdbb03139_time_elapsed_at_fee_accrual)
     cdbb03139_next_call_is_swap_occurred
     (not (not cdbb03139_swap_amount_in_includes_accrued_fee))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
