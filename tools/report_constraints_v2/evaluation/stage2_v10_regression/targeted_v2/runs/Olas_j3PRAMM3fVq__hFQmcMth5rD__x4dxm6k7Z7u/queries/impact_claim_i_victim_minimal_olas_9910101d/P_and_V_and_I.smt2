; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c95baa820_amount_out_minimum () Int)
(declare-fun c95baa820_fair_olas_value () Int)
(declare-fun c95baa820_pending_buyback_observable () Bool)
(declare-fun c95baa820_post_swap_validation_present () Bool)
(declare-fun c95baa820_sqrt_price_limit_x96 () Int)
(declare-fun c95baa820_victim_received_olas () Int)
(assert
 (= c95baa820_amount_out_minimum c95baa820_amount_out_minimum))
(assert
 (= c95baa820_fair_olas_value c95baa820_fair_olas_value))
(assert
 (= c95baa820_pending_buyback_observable c95baa820_pending_buyback_observable))
(assert
 (= c95baa820_post_swap_validation_present c95baa820_post_swap_validation_present))
(assert
 (= c95baa820_sqrt_price_limit_x96 c95baa820_sqrt_price_limit_x96))
(assert
 (= c95baa820_victim_received_olas c95baa820_victim_received_olas))
(define-fun report_preconditions () Bool (and c95baa820_pending_buyback_observable
     (= 1 c95baa820_amount_out_minimum)
     (= 0 c95baa820_sqrt_price_limit_x96)
     (not c95baa820_post_swap_validation_present)))
(define-fun report_safety () Bool (=> (and c95baa820_pending_buyback_observable
         (= 1 c95baa820_amount_out_minimum)
         (= 0 c95baa820_sqrt_price_limit_x96)
         (not c95baa820_post_swap_validation_present))
    (>= c95baa820_victim_received_olas c95baa820_fair_olas_value)))
(define-fun report_effects () Bool (and c95baa820_pending_buyback_observable
     (= 1 c95baa820_amount_out_minimum)
     (= 0 c95baa820_sqrt_price_limit_x96)
     (not c95baa820_post_swap_validation_present)
     (not (>= c95baa820_victim_received_olas c95baa820_fair_olas_value))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
