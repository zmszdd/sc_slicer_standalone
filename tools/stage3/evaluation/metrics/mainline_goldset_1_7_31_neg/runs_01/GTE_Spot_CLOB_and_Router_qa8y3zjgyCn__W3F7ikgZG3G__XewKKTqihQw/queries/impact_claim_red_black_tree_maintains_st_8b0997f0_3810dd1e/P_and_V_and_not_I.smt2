; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce90b5f6a_level_retained_without_live_orders () Bool)
(declare-fun ce90b5f6a_price_level_has_live_orders () Bool)
(declare-fun ce90b5f6a_price_level_present_in_tree () Bool)
(declare-fun ce90b5f6a_stale_price_level_retained () Bool)
(assert
 (= ce90b5f6a_level_retained_without_live_orders ce90b5f6a_level_retained_without_live_orders))
(assert
 (= ce90b5f6a_price_level_has_live_orders ce90b5f6a_price_level_has_live_orders))
(assert
 (= ce90b5f6a_price_level_present_in_tree ce90b5f6a_price_level_present_in_tree))
(assert
 (= ce90b5f6a_stale_price_level_retained ce90b5f6a_stale_price_level_retained))
(define-fun report_preconditions () Bool (and (not ce90b5f6a_price_level_has_live_orders)
     ce90b5f6a_price_level_present_in_tree))
(define-fun report_safety () Bool (=> ce90b5f6a_price_level_present_in_tree
    (= ce90b5f6a_level_retained_without_live_orders
       ce90b5f6a_price_level_has_live_orders)))
(define-fun report_effects () Bool (and ce90b5f6a_price_level_present_in_tree
     (not (= ce90b5f6a_level_retained_without_live_orders
             ce90b5f6a_price_level_has_live_orders))
     ce90b5f6a_stale_price_level_retained))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
