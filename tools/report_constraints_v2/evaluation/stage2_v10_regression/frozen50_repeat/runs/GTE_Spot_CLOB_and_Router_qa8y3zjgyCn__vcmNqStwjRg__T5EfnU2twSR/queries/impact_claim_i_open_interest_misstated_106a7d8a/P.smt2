; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce57052bf_corruption_persists () Bool)
(declare-fun ce57052bf_new_order_appended () Bool)
(declare-fun ce57052bf_non_head_order_exists () Bool)
(declare-fun ce57052bf_open_interest_misstated () Bool)
(declare-fun ce57052bf_orders_addressable () Bool)
(assert
 (= ce57052bf_corruption_persists ce57052bf_corruption_persists))
(assert
 (= ce57052bf_new_order_appended ce57052bf_new_order_appended))
(assert
 (= ce57052bf_non_head_order_exists ce57052bf_non_head_order_exists))
(assert
 (= ce57052bf_open_interest_misstated ce57052bf_open_interest_misstated))
(assert
 (= ce57052bf_orders_addressable ce57052bf_orders_addressable))
(define-fun report_preconditions () Bool (and ce57052bf_non_head_order_exists
     ce57052bf_new_order_appended
     ce57052bf_corruption_persists))
(define-fun report_safety () Bool (=> (and ce57052bf_non_head_order_exists
         ce57052bf_new_order_appended
         ce57052bf_corruption_persists)
    (and ce57052bf_orders_addressable (not ce57052bf_open_interest_misstated))))
(define-fun report_effects () Bool (and ce57052bf_non_head_order_exists
     ce57052bf_new_order_appended
     ce57052bf_corruption_persists
     (not (and ce57052bf_orders_addressable
               (not ce57052bf_open_interest_misstated)))))
(assert report_preconditions)
(check-sat)
(get-model)
