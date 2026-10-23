; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c98fc1ccd_amount_out_minimum () Int)
(declare-fun c98fc1ccd_buyback_pending_in_mempool () Bool)
(declare-fun c98fc1ccd_effective_slippage_protection () Bool)
(declare-fun c98fc1ccd_post_swap_validation_present () Bool)
(declare-fun c98fc1ccd_protocol_receives_fair_value () Bool)
(declare-fun c98fc1ccd_sqrt_price_limit_x96 () Int)
(assert
 (= c98fc1ccd_amount_out_minimum c98fc1ccd_amount_out_minimum))
(assert
 (= c98fc1ccd_buyback_pending_in_mempool c98fc1ccd_buyback_pending_in_mempool))
(assert
 (= c98fc1ccd_effective_slippage_protection c98fc1ccd_effective_slippage_protection))
(assert
 (= c98fc1ccd_post_swap_validation_present c98fc1ccd_post_swap_validation_present))
(assert
 (= c98fc1ccd_protocol_receives_fair_value c98fc1ccd_protocol_receives_fair_value))
(assert
 (= c98fc1ccd_sqrt_price_limit_x96 c98fc1ccd_sqrt_price_limit_x96))
(define-fun report_preconditions () Bool (and (= 1 c98fc1ccd_amount_out_minimum)
     (= 0 c98fc1ccd_sqrt_price_limit_x96)
     (not c98fc1ccd_post_swap_validation_present)
     c98fc1ccd_buyback_pending_in_mempool))
(define-fun report_safety () Bool (=> (and (= 1 c98fc1ccd_amount_out_minimum)
         (= 0 c98fc1ccd_sqrt_price_limit_x96)
         (not c98fc1ccd_post_swap_validation_present))
    (and c98fc1ccd_effective_slippage_protection
         c98fc1ccd_protocol_receives_fair_value)))
(define-fun report_effects () Bool (and (= 1 c98fc1ccd_amount_out_minimum)
     (= 0 c98fc1ccd_sqrt_price_limit_x96)
     (not c98fc1ccd_post_swap_validation_present)
     (not (and c98fc1ccd_effective_slippage_protection
               c98fc1ccd_protocol_receives_fair_value))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
