; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd4b8e10f_amount_out_minimum () Int)
(declare-fun cd4b8e10f_extracted_swap_value_percent () Int)
(declare-fun cd4b8e10f_pending_buyback_observable () Bool)
(declare-fun cd4b8e10f_post_swap_validation_present () Bool)
(declare-fun cd4b8e10f_sqrt_price_limit_x96 () Int)
(assert
 (= cd4b8e10f_amount_out_minimum cd4b8e10f_amount_out_minimum))
(assert
 (= cd4b8e10f_extracted_swap_value_percent cd4b8e10f_extracted_swap_value_percent))
(assert
 (= cd4b8e10f_pending_buyback_observable cd4b8e10f_pending_buyback_observable))
(assert
 (= cd4b8e10f_post_swap_validation_present cd4b8e10f_post_swap_validation_present))
(assert
 (= cd4b8e10f_sqrt_price_limit_x96 cd4b8e10f_sqrt_price_limit_x96))
(define-fun report_preconditions () Bool (and cd4b8e10f_pending_buyback_observable
     (= 1 cd4b8e10f_amount_out_minimum)
     (= 0 cd4b8e10f_sqrt_price_limit_x96)
     (not cd4b8e10f_post_swap_validation_present)))
(define-fun report_safety () Bool (=> (and cd4b8e10f_pending_buyback_observable
         (= 1 cd4b8e10f_amount_out_minimum)
         (= 0 cd4b8e10f_sqrt_price_limit_x96)
         (not cd4b8e10f_post_swap_validation_present))
    (> 100 cd4b8e10f_extracted_swap_value_percent)))
(define-fun report_effects () Bool (and cd4b8e10f_pending_buyback_observable
     (= 1 cd4b8e10f_amount_out_minimum)
     (= 0 cd4b8e10f_sqrt_price_limit_x96)
     (not cd4b8e10f_post_swap_validation_present)
     (not (> 100 cd4b8e10f_extracted_swap_value_percent))))
