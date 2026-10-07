; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun spot_price_manipulated () Bool)
(declare-fun second_token_available () Bool)
(declare-fun buyback_permissionless () Bool)
(declare-fun elapsed_time () Int)
(declare-fun swap_executed_at_manipulated_price () Bool)
(assert
 (= spot_price_manipulated spot_price_manipulated))
(assert
 (= second_token_available second_token_available))
(assert
 (= buyback_permissionless buyback_permissionless))
(assert
 (= elapsed_time elapsed_time))
(assert
 (= swap_executed_at_manipulated_price swap_executed_at_manipulated_price))
(define-fun report_preconditions () Bool (and spot_price_manipulated
     second_token_available
     buyback_permissionless
     (< 0 elapsed_time)))
(define-fun report_safety () Bool (=> (and spot_price_manipulated
         second_token_available
         buyback_permissionless
         (< 0 elapsed_time))
    (not swap_executed_at_manipulated_price)))
(define-fun report_effects () Bool (and spot_price_manipulated
     second_token_available
     buyback_permissionless
     (< 0 elapsed_time)
     (not (not swap_executed_at_manipulated_price))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
