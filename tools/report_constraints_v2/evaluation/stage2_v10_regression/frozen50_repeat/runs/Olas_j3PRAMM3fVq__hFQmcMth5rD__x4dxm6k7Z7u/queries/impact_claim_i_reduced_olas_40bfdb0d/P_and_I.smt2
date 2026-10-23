; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce4ca984c_amount_out_minimum () Int)
(declare-fun ce4ca984c_buyback_tx_public () Bool)
(declare-fun ce4ca984c_olas_fair_value () Int)
(declare-fun ce4ca984c_olas_received () Int)
(declare-fun ce4ca984c_sqrt_price_limit_x96 () Int)
(assert
 (= ce4ca984c_amount_out_minimum ce4ca984c_amount_out_minimum))
(assert
 (= ce4ca984c_buyback_tx_public ce4ca984c_buyback_tx_public))
(assert
 (= ce4ca984c_olas_fair_value ce4ca984c_olas_fair_value))
(assert
 (= ce4ca984c_olas_received ce4ca984c_olas_received))
(assert
 (= ce4ca984c_sqrt_price_limit_x96 ce4ca984c_sqrt_price_limit_x96))
(define-fun report_preconditions () Bool (and ce4ca984c_buyback_tx_public
     (= 1 ce4ca984c_amount_out_minimum)
     (= 0 ce4ca984c_sqrt_price_limit_x96)))
(define-fun report_safety () Bool (=> (and ce4ca984c_buyback_tx_public
         (= 1 ce4ca984c_amount_out_minimum)
         (= 0 ce4ca984c_sqrt_price_limit_x96))
    (>= ce4ca984c_olas_received ce4ca984c_olas_fair_value)))
(define-fun report_effects () Bool (and ce4ca984c_buyback_tx_public
     (= 1 ce4ca984c_amount_out_minimum)
     (= 0 ce4ca984c_sqrt_price_limit_x96)
     (not (>= ce4ca984c_olas_received ce4ca984c_olas_fair_value))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
