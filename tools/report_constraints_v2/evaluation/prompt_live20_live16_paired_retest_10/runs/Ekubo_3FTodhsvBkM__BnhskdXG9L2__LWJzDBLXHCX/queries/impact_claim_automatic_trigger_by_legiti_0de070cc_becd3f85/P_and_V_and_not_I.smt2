; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caebc106e_pool_initialized_at_tick_zero () Bool)
(declare-fun caebc106e_sqrt_ratio_equals_limit () Bool)
(declare-fun caebc106e_swap_reverted () Bool)
(declare-fun caebc106e_triggered_by_legitimate_swaps () Bool)
(declare-fun caebc106e_victim_swap_msg_value () Int)
(assert
 (= caebc106e_pool_initialized_at_tick_zero caebc106e_pool_initialized_at_tick_zero))
(assert
 (= caebc106e_sqrt_ratio_equals_limit caebc106e_sqrt_ratio_equals_limit))
(assert
 (= caebc106e_swap_reverted caebc106e_swap_reverted))
(assert
 (= caebc106e_triggered_by_legitimate_swaps caebc106e_triggered_by_legitimate_swaps))
(assert
 (= caebc106e_victim_swap_msg_value caebc106e_victim_swap_msg_value))
(define-fun report_preconditions () Bool (and caebc106e_pool_initialized_at_tick_zero
     (= 10 caebc106e_victim_swap_msg_value)))
(define-fun report_safety () Bool (=> (and caebc106e_sqrt_ratio_equals_limit
         (< 0 caebc106e_victim_swap_msg_value))
    caebc106e_swap_reverted))
(define-fun report_effects () Bool caebc106e_triggered_by_legitimate_swaps)
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
