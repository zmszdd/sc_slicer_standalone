; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun order_posted () Bool)
(declare-fun same_price_order_exists () Bool)
(declare-fun stored_prev_order_id () Int)
(declare-fun stored_next_order_id () Int)
(declare-fun zero_id () Int)
(assert
 (= order_posted order_posted))
(assert
 (= same_price_order_exists same_price_order_exists))
(assert
 (= stored_prev_order_id stored_prev_order_id))
(assert
 (= stored_next_order_id stored_next_order_id))
(assert
 (= zero_id zero_id))
(define-fun report_preconditions () Bool (and order_posted same_price_order_exists))
(define-fun report_safety () Bool (=> (and order_posted same_price_order_exists)
    (and (distinct stored_prev_order_id zero_id)
         (distinct stored_next_order_id zero_id))))
(define-fun report_effects () Bool (and order_posted
     same_price_order_exists
     (not (and (distinct stored_prev_order_id zero_id)
               (distinct stored_next_order_id zero_id)))))
