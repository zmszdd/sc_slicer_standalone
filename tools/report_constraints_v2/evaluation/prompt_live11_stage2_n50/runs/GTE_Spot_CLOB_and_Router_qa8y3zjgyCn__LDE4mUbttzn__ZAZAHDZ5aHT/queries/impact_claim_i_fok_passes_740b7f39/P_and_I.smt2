; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c61a46d92_amount_is_base () Bool)
(declare-fun c61a46d92_fok_marked_filled_with_dust () Bool)
(declare-fun c61a46d92_lot_size_in_base () Int)
(declare-fun c61a46d92_maker_base () Int)
(declare-fun c61a46d92_normalized_price () Int)
(declare-fun c61a46d92_remaining_quote () Int)
(assert
 (= c61a46d92_amount_is_base c61a46d92_amount_is_base))
(assert
 (= c61a46d92_fok_marked_filled_with_dust c61a46d92_fok_marked_filled_with_dust))
(assert
 (= c61a46d92_lot_size_in_base c61a46d92_lot_size_in_base))
(assert
 (= c61a46d92_maker_base c61a46d92_maker_base))
(assert
 (= c61a46d92_normalized_price c61a46d92_normalized_price))
(assert
 (= c61a46d92_remaining_quote c61a46d92_remaining_quote))
(define-fun report_preconditions () Bool (and (not c61a46d92_amount_is_base)
     (= 1000000000000000000 c61a46d92_lot_size_in_base)
     (= 2500000000000000000 c61a46d92_remaining_quote)
     (= 3000000000000000000 c61a46d92_maker_base)
     (= 1000000000000000000 c61a46d92_normalized_price)))
(define-fun report_safety () Bool (=> (and (not c61a46d92_amount_is_base)
         (= 1000000000000000000 c61a46d92_lot_size_in_base)
         (= 2500000000000000000 c61a46d92_remaining_quote)
         (= 3000000000000000000 c61a46d92_maker_base)
         (= 1000000000000000000 c61a46d92_normalized_price))
    (not c61a46d92_fok_marked_filled_with_dust)))
(define-fun report_effects () Bool (and (not c61a46d92_amount_is_base)
     (= 1000000000000000000 c61a46d92_lot_size_in_base)
     (= 2500000000000000000 c61a46d92_remaining_quote)
     (= 3000000000000000000 c61a46d92_maker_base)
     (= 1000000000000000000 c61a46d92_normalized_price)
     (not (not c61a46d92_fok_marked_filled_with_dust))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
