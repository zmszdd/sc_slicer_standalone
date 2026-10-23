; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cde065802_head_order_id () Int)
(declare-fun cde065802_level_corrupted () Bool)
(declare-fun cde065802_new_order_appended () Bool)
(declare-fun cde065802_num_orders () Int)
(declare-fun cde065802_orders_stored_in_list () Bool)
(declare-fun cde065802_zero_order_id () Int)
(assert
 (= cde065802_head_order_id cde065802_head_order_id))
(assert
 (= cde065802_level_corrupted cde065802_level_corrupted))
(assert
 (= cde065802_new_order_appended cde065802_new_order_appended))
(assert
 (= cde065802_num_orders cde065802_num_orders))
(assert
 (= cde065802_orders_stored_in_list cde065802_orders_stored_in_list))
(assert
 (= cde065802_zero_order_id cde065802_zero_order_id))
(define-fun report_preconditions () Bool (and cde065802_orders_stored_in_list cde065802_new_order_appended))
(define-fun report_safety () Bool (=> (< 0 cde065802_num_orders)
    (or (distinct cde065802_head_order_id cde065802_zero_order_id)
        (not cde065802_level_corrupted))))
(define-fun report_effects () Bool (and (< 0 cde065802_num_orders)
     (not (or (distinct cde065802_head_order_id cde065802_zero_order_id)
              (not cde065802_level_corrupted)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
