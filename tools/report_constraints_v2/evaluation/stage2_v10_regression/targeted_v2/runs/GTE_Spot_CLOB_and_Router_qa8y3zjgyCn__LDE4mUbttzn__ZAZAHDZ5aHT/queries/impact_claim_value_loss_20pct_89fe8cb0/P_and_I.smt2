; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c54408a04_amount_is_base () Bool)
(declare-fun c54408a04_base_delta () Int)
(declare-fun c54408a04_expected_value_loss_pct () Int)
(declare-fun c54408a04_lot_size_in_base () Int)
(declare-fun c54408a04_maker_base_available () Int)
(declare-fun c54408a04_matched_base () Int)
(declare-fun c54408a04_remaining_quote_amount () Int)
(assert
 (= c54408a04_amount_is_base c54408a04_amount_is_base))
(assert
 (= c54408a04_base_delta c54408a04_base_delta))
(assert
 (= c54408a04_expected_value_loss_pct c54408a04_expected_value_loss_pct))
(assert
 (= c54408a04_lot_size_in_base c54408a04_lot_size_in_base))
(assert
 (= c54408a04_maker_base_available c54408a04_maker_base_available))
(assert
 (= c54408a04_matched_base c54408a04_matched_base))
(assert
 (= c54408a04_remaining_quote_amount c54408a04_remaining_quote_amount))
(define-fun report_preconditions () Bool (and (not c54408a04_amount_is_base)
     (= 1000000000000000000 c54408a04_lot_size_in_base)
     (= 2500000000000000000 c54408a04_remaining_quote_amount)
     (= 3000000000000000000 c54408a04_maker_base_available)
     (= 2000000000000000000 c54408a04_base_delta)
     (= 2500000000000000000 c54408a04_matched_base)
     (distinct c54408a04_base_delta c54408a04_matched_base)))
(define-fun report_safety () Bool (=> (and (not c54408a04_amount_is_base)
         (= 1000000000000000000 c54408a04_lot_size_in_base)
         (= 2500000000000000000 c54408a04_remaining_quote_amount)
         (= 3000000000000000000 c54408a04_maker_base_available))
    (and (= c54408a04_base_delta c54408a04_matched_base)
         (= 0 c54408a04_expected_value_loss_pct))))
(define-fun report_effects () Bool (and (not c54408a04_amount_is_base)
     (= 1000000000000000000 c54408a04_lot_size_in_base)
     (= 2500000000000000000 c54408a04_remaining_quote_amount)
     (= 3000000000000000000 c54408a04_maker_base_available)
     (not (and (= c54408a04_base_delta c54408a04_matched_base)
               (= 0 c54408a04_expected_value_loss_pct)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
