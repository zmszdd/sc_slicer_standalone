; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c832f7903_slippage_protection_present () Bool)
(declare-fun c832f7903_swap_executed_after_deadline () Bool)
(declare-fun c832f7903_swap_submitted () Bool)
(declare-fun c832f7903_trade_unwanted () Bool)
(declare-fun c832f7903_user_deadline_specifiable () Bool)
(assert
 (= c832f7903_slippage_protection_present c832f7903_slippage_protection_present))
(assert
 (= c832f7903_swap_executed_after_deadline c832f7903_swap_executed_after_deadline))
(assert
 (= c832f7903_swap_submitted c832f7903_swap_submitted))
(assert
 (= c832f7903_trade_unwanted c832f7903_trade_unwanted))
(assert
 (= c832f7903_user_deadline_specifiable c832f7903_user_deadline_specifiable))
(define-fun report_preconditions () Bool (and c832f7903_swap_submitted
     (not c832f7903_user_deadline_specifiable)
     c832f7903_slippage_protection_present))
(define-fun report_safety () Bool (=> (and c832f7903_swap_submitted
         (not c832f7903_user_deadline_specifiable)
         c832f7903_slippage_protection_present)
    (and (not c832f7903_swap_executed_after_deadline)
         (not c832f7903_trade_unwanted))))
(define-fun report_effects () Bool (and c832f7903_swap_submitted
     (not c832f7903_user_deadline_specifiable)
     c832f7903_slippage_protection_present
     (not (and (not c832f7903_swap_executed_after_deadline)
               (not c832f7903_trade_unwanted)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
