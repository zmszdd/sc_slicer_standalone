; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun lot_size_in_base () Int)
(declare-fun resting_sell_amount () Int)
(declare-fun fok_buy_amount () Int)
(declare-fun filled_amount () Int)
(declare-fun new_order_amount () Int)
(declare-fun fok_not_filled_revert () Bool)
(assert
 (= lot_size_in_base lot_size_in_base))
(assert
 (= resting_sell_amount resting_sell_amount))
(assert
 (= fok_buy_amount fok_buy_amount))
(assert
 (= filled_amount filled_amount))
(assert
 (= new_order_amount new_order_amount))
(assert
 (= fok_not_filled_revert fok_not_filled_revert))
(define-fun report_preconditions () Bool (and (= 1 lot_size_in_base)
     (<= 100 resting_sell_amount)
     (>= 101 fok_buy_amount)))
(define-fun report_safety () Bool (=> (= new_order_amount (- fok_buy_amount filled_amount))
    (=> (and (<= 100 filled_amount) (< new_order_amount lot_size_in_base))
        (not fok_not_filled_revert))))
(define-fun report_effects () Bool (and (= new_order_amount (- fok_buy_amount filled_amount))
     (<= 100 filled_amount)
     (< new_order_amount lot_size_in_base)
     (not (not fok_not_filled_revert))))
