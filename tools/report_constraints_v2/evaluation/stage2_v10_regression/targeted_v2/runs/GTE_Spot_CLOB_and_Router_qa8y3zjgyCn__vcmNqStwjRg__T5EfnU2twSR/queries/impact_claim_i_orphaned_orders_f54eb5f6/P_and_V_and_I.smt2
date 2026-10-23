; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca8e7df36_forward_and_back_links_updated () Bool)
(declare-fun ca8e7df36_order_counted_in_open_interest () Bool)
(declare-fun ca8e7df36_order_in_price_level_list () Bool)
(declare-fun ca8e7df36_order_reachable () Bool)
(assert
 (= ca8e7df36_forward_and_back_links_updated ca8e7df36_forward_and_back_links_updated))
(assert
 (= ca8e7df36_order_counted_in_open_interest ca8e7df36_order_counted_in_open_interest))
(assert
 (= ca8e7df36_order_in_price_level_list ca8e7df36_order_in_price_level_list))
(assert
 (= ca8e7df36_order_reachable ca8e7df36_order_reachable))
(define-fun report_preconditions () Bool (and ca8e7df36_order_in_price_level_list
     ca8e7df36_forward_and_back_links_updated))
(define-fun report_safety () Bool (=> (and ca8e7df36_order_in_price_level_list
         ca8e7df36_forward_and_back_links_updated)
    (and ca8e7df36_order_reachable
         (= ca8e7df36_order_counted_in_open_interest ca8e7df36_order_reachable))))
(define-fun report_effects () Bool (and ca8e7df36_order_in_price_level_list
     ca8e7df36_forward_and_back_links_updated
     (not (and ca8e7df36_order_reachable
               (= ca8e7df36_order_counted_in_open_interest
                  ca8e7df36_order_reachable)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
