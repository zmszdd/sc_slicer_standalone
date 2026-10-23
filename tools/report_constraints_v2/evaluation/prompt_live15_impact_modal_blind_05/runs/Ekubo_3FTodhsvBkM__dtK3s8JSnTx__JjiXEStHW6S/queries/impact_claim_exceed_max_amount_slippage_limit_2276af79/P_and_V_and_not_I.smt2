; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfe465fd7_pending_virtual_orders_exist () Bool)
(declare-fun cfe465fd7_spent_exceeds_max_amounts () Bool)
(declare-fun cfe465fd7_sqrt_ratio_updated_by_orders () Bool)
(declare-fun cfe465fd7_user_supplies_max_amounts () Bool)
(assert
 (= cfe465fd7_pending_virtual_orders_exist cfe465fd7_pending_virtual_orders_exist))
(assert
 (= cfe465fd7_spent_exceeds_max_amounts cfe465fd7_spent_exceeds_max_amounts))
(assert
 (= cfe465fd7_sqrt_ratio_updated_by_orders cfe465fd7_sqrt_ratio_updated_by_orders))
(assert
 (= cfe465fd7_user_supplies_max_amounts cfe465fd7_user_supplies_max_amounts))
(define-fun report_preconditions () Bool (and cfe465fd7_pending_virtual_orders_exist
     cfe465fd7_sqrt_ratio_updated_by_orders
     cfe465fd7_user_supplies_max_amounts))
(define-fun report_safety () Bool (=> (and cfe465fd7_pending_virtual_orders_exist
         cfe465fd7_sqrt_ratio_updated_by_orders
         cfe465fd7_user_supplies_max_amounts)
    (not cfe465fd7_spent_exceeds_max_amounts)))
(define-fun report_effects () Bool (and cfe465fd7_pending_virtual_orders_exist
     cfe465fd7_sqrt_ratio_updated_by_orders
     cfe465fd7_user_supplies_max_amounts
     (not (not cfe465fd7_spent_exceeds_max_amounts))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
