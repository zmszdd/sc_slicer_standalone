; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c152498e8_amount_is_quote () Bool)
(declare-fun c152498e8_is_fok_order () Bool)
(declare-fun c152498e8_lot_size_in_base () Int)
(declare-fun c152498e8_order_amount_reduced () Int)
(declare-fun c152498e8_quote_amount_traded () Int)
(declare-fun c152498e8_remaining_quote_before () Int)
(assert
 (= c152498e8_amount_is_quote c152498e8_amount_is_quote))
(assert
 (= c152498e8_is_fok_order c152498e8_is_fok_order))
(assert
 (= c152498e8_lot_size_in_base c152498e8_lot_size_in_base))
(assert
 (= c152498e8_order_amount_reduced c152498e8_order_amount_reduced))
(assert
 (= c152498e8_quote_amount_traded c152498e8_quote_amount_traded))
(assert
 (= c152498e8_remaining_quote_before c152498e8_remaining_quote_before))
(define-fun report_preconditions () Bool (and c152498e8_amount_is_quote
     (= 1000000000000000000 c152498e8_lot_size_in_base)
     (= 2500000000000000000 c152498e8_remaining_quote_before)
     c152498e8_is_fok_order))
(define-fun report_safety () Bool (=> (and c152498e8_amount_is_quote c152498e8_is_fok_order)
    (<= c152498e8_order_amount_reduced c152498e8_quote_amount_traded)))
(define-fun report_effects () Bool (and c152498e8_amount_is_quote
     c152498e8_is_fok_order
     (not (<= c152498e8_order_amount_reduced c152498e8_quote_amount_traded))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
