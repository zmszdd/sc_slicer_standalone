; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9cf4cb71_expiring_orders_removed_with_full_refund () Bool)
(declare-fun c9cf4cb71_fees_applied_only_on_match () Bool)
(declare-fun c9cf4cb71_maker_fee_percent () Int)
(declare-fun c9cf4cb71_order_placement_charges_fee () Bool)
(declare-fun c9cf4cb71_victim_paid_fee_percent () Int)
(assert
 (= c9cf4cb71_expiring_orders_removed_with_full_refund c9cf4cb71_expiring_orders_removed_with_full_refund))
(assert
 (= c9cf4cb71_fees_applied_only_on_match c9cf4cb71_fees_applied_only_on_match))
(assert
 (= c9cf4cb71_maker_fee_percent c9cf4cb71_maker_fee_percent))
(assert
 (= c9cf4cb71_order_placement_charges_fee c9cf4cb71_order_placement_charges_fee))
(assert
 (= c9cf4cb71_victim_paid_fee_percent c9cf4cb71_victim_paid_fee_percent))
(define-fun report_preconditions () Bool (and (not c9cf4cb71_order_placement_charges_fee)
     c9cf4cb71_fees_applied_only_on_match
     c9cf4cb71_expiring_orders_removed_with_full_refund))
(define-fun report_safety () Bool (=> (and (> c9cf4cb71_victim_paid_fee_percent c9cf4cb71_maker_fee_percent)
         (= 5 c9cf4cb71_victim_paid_fee_percent)
         (= 3 c9cf4cb71_maker_fee_percent))
    (=> (and (not c9cf4cb71_order_placement_charges_fee)
             c9cf4cb71_fees_applied_only_on_match
             c9cf4cb71_expiring_orders_removed_with_full_refund)
        (<= c9cf4cb71_victim_paid_fee_percent c9cf4cb71_maker_fee_percent))))
(define-fun report_effects () Bool (and (> c9cf4cb71_victim_paid_fee_percent c9cf4cb71_maker_fee_percent)
     (= 5 c9cf4cb71_victim_paid_fee_percent)
     (= 3 c9cf4cb71_maker_fee_percent)
     (not c9cf4cb71_order_placement_charges_fee)
     c9cf4cb71_fees_applied_only_on_match
     c9cf4cb71_expiring_orders_removed_with_full_refund
     (not (<= c9cf4cb71_victim_paid_fee_percent c9cf4cb71_maker_fee_percent))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
