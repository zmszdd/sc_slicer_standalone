; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c19cc10b5_cap_enforced_flag () Bool)
(declare-fun c19cc10b5_expired_orders_resident () Bool)
(declare-fun c19cc10b5_valid_order_rejected () Bool)
(assert
 (= c19cc10b5_cap_enforced_flag c19cc10b5_cap_enforced_flag))
(assert
 (= c19cc10b5_expired_orders_resident c19cc10b5_expired_orders_resident))
(assert
 (= c19cc10b5_valid_order_rejected c19cc10b5_valid_order_rejected))
(define-fun report_preconditions () Bool (and c19cc10b5_cap_enforced_flag c19cc10b5_expired_orders_resident))
(define-fun report_safety () Bool (=> (and c19cc10b5_cap_enforced_flag c19cc10b5_expired_orders_resident)
    (not c19cc10b5_valid_order_rejected)))
(define-fun report_effects () Bool (and c19cc10b5_cap_enforced_flag
     c19cc10b5_expired_orders_resident
     (not (not c19cc10b5_valid_order_rejected))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
