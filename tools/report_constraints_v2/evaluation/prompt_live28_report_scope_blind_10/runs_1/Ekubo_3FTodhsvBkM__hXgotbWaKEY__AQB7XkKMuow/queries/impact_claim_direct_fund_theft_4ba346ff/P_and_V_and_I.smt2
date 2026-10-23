; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c73b673bd_amount_sold_after_update () Int)
(declare-fun c73b673bd_amount_sold_expected_pre_start () Int)
(declare-fun c73b673bd_block_timestamp () Int)
(declare-fun c73b673bd_handle_forward_data_unchecked () Bool)
(declare-fun c73b673bd_inflated_amount_sold_observed () Bool)
(declare-fun c73b673bd_order_start_time () Int)
(assert
 (= c73b673bd_amount_sold_after_update c73b673bd_amount_sold_after_update))
(assert
 (= c73b673bd_amount_sold_expected_pre_start c73b673bd_amount_sold_expected_pre_start))
(assert
 (= c73b673bd_block_timestamp c73b673bd_block_timestamp))
(assert
 (= c73b673bd_handle_forward_data_unchecked c73b673bd_handle_forward_data_unchecked))
(assert
 (= c73b673bd_inflated_amount_sold_observed c73b673bd_inflated_amount_sold_observed))
(assert
 (= c73b673bd_order_start_time c73b673bd_order_start_time))
(define-fun report_preconditions () Bool (and (< c73b673bd_block_timestamp c73b673bd_order_start_time)
     c73b673bd_handle_forward_data_unchecked))
(define-fun report_safety () Bool (let ((a!1 (=> c73b673bd_inflated_amount_sold_observed
               (=> (and (< c73b673bd_block_timestamp c73b673bd_order_start_time)
                        c73b673bd_handle_forward_data_unchecked)
                   (= c73b673bd_amount_sold_after_update
                      c73b673bd_amount_sold_expected_pre_start)))))
  (=> (= 0 c73b673bd_amount_sold_expected_pre_start) a!1)))
(define-fun report_effects () Bool (and (= 0 c73b673bd_amount_sold_expected_pre_start)
     c73b673bd_inflated_amount_sold_observed
     (< c73b673bd_block_timestamp c73b673bd_order_start_time)
     c73b673bd_handle_forward_data_unchecked
     (not (= c73b673bd_amount_sold_after_update
             c73b673bd_amount_sold_expected_pre_start))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
