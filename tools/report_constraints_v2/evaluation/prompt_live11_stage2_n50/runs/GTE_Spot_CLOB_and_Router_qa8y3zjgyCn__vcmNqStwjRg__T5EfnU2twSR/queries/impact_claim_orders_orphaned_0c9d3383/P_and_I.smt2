; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c95d8b175_non_head_order_present () Bool)
(declare-fun c95d8b175_order_appended () Bool)
(declare-fun c95d8b175_order_counted_in_open_interest () Bool)
(declare-fun c95d8b175_order_reachable () Bool)
(assert
 (= c95d8b175_non_head_order_present c95d8b175_non_head_order_present))
(assert
 (= c95d8b175_order_appended c95d8b175_order_appended))
(assert
 (= c95d8b175_order_counted_in_open_interest c95d8b175_order_counted_in_open_interest))
(assert
 (= c95d8b175_order_reachable c95d8b175_order_reachable))
(define-fun report_preconditions () Bool (and c95d8b175_order_appended c95d8b175_non_head_order_present))
(define-fun report_safety () Bool (=> (and c95d8b175_order_appended c95d8b175_non_head_order_present)
    (and c95d8b175_order_reachable c95d8b175_order_counted_in_open_interest)))
(define-fun report_effects () Bool (and c95d8b175_order_appended
     c95d8b175_non_head_order_present
     (not (and c95d8b175_order_reachable
               c95d8b175_order_counted_in_open_interest))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
