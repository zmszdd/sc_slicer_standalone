; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf0cb1a66_is_reduce_only_order () Bool)
(declare-fun cf0cb1a66_no_collateral_involved () Bool)
(declare-fun cf0cb1a66_order_amount_tiny () Bool)
(declare-fun cf0cb1a66_order_price_arbitrarily_large () Bool)
(declare-fun cf0cb1a66_other_buy_order_reverts () Bool)
(declare-fun cf0cb1a66_quote_oi_increment_from_reduce_only () Int)
(declare-fun cf0cb1a66_quote_oi_massively_inflated () Bool)
(declare-fun cf0cb1a66_zero_oi_increment () Int)
(assert
 (= cf0cb1a66_is_reduce_only_order cf0cb1a66_is_reduce_only_order))
(assert
 (= cf0cb1a66_no_collateral_involved cf0cb1a66_no_collateral_involved))
(assert
 (= cf0cb1a66_order_amount_tiny cf0cb1a66_order_amount_tiny))
(assert
 (= cf0cb1a66_order_price_arbitrarily_large cf0cb1a66_order_price_arbitrarily_large))
(assert
 (= cf0cb1a66_other_buy_order_reverts cf0cb1a66_other_buy_order_reverts))
(assert
 (= cf0cb1a66_quote_oi_increment_from_reduce_only cf0cb1a66_quote_oi_increment_from_reduce_only))
(assert
 (= cf0cb1a66_quote_oi_massively_inflated cf0cb1a66_quote_oi_massively_inflated))
(assert
 (= cf0cb1a66_zero_oi_increment cf0cb1a66_zero_oi_increment))
(define-fun report_preconditions () Bool (and cf0cb1a66_is_reduce_only_order
     cf0cb1a66_order_amount_tiny
     cf0cb1a66_order_price_arbitrarily_large
     cf0cb1a66_no_collateral_involved))
(define-fun report_safety () Bool (=> cf0cb1a66_is_reduce_only_order
    (= cf0cb1a66_quote_oi_increment_from_reduce_only
       cf0cb1a66_zero_oi_increment)))
(define-fun report_effects () Bool (and cf0cb1a66_is_reduce_only_order
     (not (= cf0cb1a66_quote_oi_increment_from_reduce_only
             cf0cb1a66_zero_oi_increment))
     cf0cb1a66_quote_oi_massively_inflated
     cf0cb1a66_other_buy_order_reverts))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
