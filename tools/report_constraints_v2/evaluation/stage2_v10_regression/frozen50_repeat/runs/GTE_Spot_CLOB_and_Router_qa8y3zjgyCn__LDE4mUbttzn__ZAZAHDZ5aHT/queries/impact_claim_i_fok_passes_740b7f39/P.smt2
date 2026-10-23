; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c61a46d92_fok_validation_passed () Bool)
(declare-fun c61a46d92_lot_size_in_base () Int)
(declare-fun c61a46d92_maker_base_liquidity () Int)
(declare-fun c61a46d92_order_is_quote_denominated () Bool)
(declare-fun c61a46d92_remaining_quote_amount () Int)
(declare-fun c61a46d92_unfilled_quote_remains () Bool)
(assert
 (= c61a46d92_fok_validation_passed c61a46d92_fok_validation_passed))
(assert
 (= c61a46d92_lot_size_in_base c61a46d92_lot_size_in_base))
(assert
 (= c61a46d92_maker_base_liquidity c61a46d92_maker_base_liquidity))
(assert
 (= c61a46d92_order_is_quote_denominated c61a46d92_order_is_quote_denominated))
(assert
 (= c61a46d92_remaining_quote_amount c61a46d92_remaining_quote_amount))
(assert
 (= c61a46d92_unfilled_quote_remains c61a46d92_unfilled_quote_remains))
(define-fun report_preconditions () Bool (and c61a46d92_order_is_quote_denominated
     (= 1000000000000000000 c61a46d92_lot_size_in_base)
     (= 2500000000000000000 c61a46d92_remaining_quote_amount)
     (= 3000000000000000000 c61a46d92_maker_base_liquidity)))
(define-fun report_safety () Bool (=> (and c61a46d92_order_is_quote_denominated
         (= 1000000000000000000 c61a46d92_lot_size_in_base)
         (= 2500000000000000000 c61a46d92_remaining_quote_amount)
         (= 3000000000000000000 c61a46d92_maker_base_liquidity))
    (or (not c61a46d92_fok_validation_passed)
        (not c61a46d92_unfilled_quote_remains))))
(define-fun report_effects () Bool (and c61a46d92_order_is_quote_denominated
     (= 1000000000000000000 c61a46d92_lot_size_in_base)
     (= 2500000000000000000 c61a46d92_remaining_quote_amount)
     (= 3000000000000000000 c61a46d92_maker_base_liquidity)
     (not (or (not c61a46d92_fok_validation_passed)
              (not c61a46d92_unfilled_quote_remains)))))
(assert report_preconditions)
(check-sat)
(get-model)
