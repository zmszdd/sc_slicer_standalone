; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6bf08091_amount_is_base () Bool)
(declare-fun c6bf08091_base_delta () Int)
(declare-fun c6bf08091_base_received () Int)
(declare-fun c6bf08091_lot_size_in_base () Int)
(declare-fun c6bf08091_maker_base_available () Int)
(declare-fun c6bf08091_matched_base () Int)
(declare-fun c6bf08091_order_marked_fully_filled () Bool)
(declare-fun c6bf08091_remaining_quote () Int)
(assert
 (= c6bf08091_amount_is_base c6bf08091_amount_is_base))
(assert
 (= c6bf08091_base_delta c6bf08091_base_delta))
(assert
 (= c6bf08091_base_received c6bf08091_base_received))
(assert
 (= c6bf08091_lot_size_in_base c6bf08091_lot_size_in_base))
(assert
 (= c6bf08091_maker_base_available c6bf08091_maker_base_available))
(assert
 (= c6bf08091_matched_base c6bf08091_matched_base))
(assert
 (= c6bf08091_order_marked_fully_filled c6bf08091_order_marked_fully_filled))
(assert
 (= c6bf08091_remaining_quote c6bf08091_remaining_quote))
(define-fun report_preconditions () Bool (and (not c6bf08091_amount_is_base)
     (= 1000000000000000000 c6bf08091_lot_size_in_base)
     (= 2500000000000000000 c6bf08091_remaining_quote)
     (= 3000000000000000000 c6bf08091_maker_base_available)
     (distinct c6bf08091_base_delta c6bf08091_matched_base)))
(define-fun report_safety () Bool (=> (and (not c6bf08091_amount_is_base)
         (= 2500000000000000000 c6bf08091_remaining_quote)
         (= 3000000000000000000 c6bf08091_maker_base_available))
    (or (and (>= c6bf08091_base_received c6bf08091_matched_base)
             (not c6bf08091_order_marked_fully_filled))
        (and (< c6bf08091_base_received c6bf08091_matched_base)
             c6bf08091_order_marked_fully_filled))))
(define-fun report_effects () Bool (let ((a!1 (not (or (and (>= c6bf08091_base_received c6bf08091_matched_base)
                         (not c6bf08091_order_marked_fully_filled))
                    (and (< c6bf08091_base_received c6bf08091_matched_base)
                         c6bf08091_order_marked_fully_filled)))))
  (and (not c6bf08091_amount_is_base)
       (= 2500000000000000000 c6bf08091_remaining_quote)
       (= 3000000000000000000 c6bf08091_maker_base_available)
       a!1)))
(assert report_preconditions)
(check-sat)
(get-model)
