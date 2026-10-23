; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7bba3822_deadline_param_supported () Bool)
(declare-fun c7bba3822_executed_after_significant_delay () Bool)
(declare-fun c7bba3822_slippage_only_protection () Bool)
(declare-fun c7bba3822_unwanted_trade_occurred () Bool)
(assert
 (= c7bba3822_deadline_param_supported c7bba3822_deadline_param_supported))
(assert
 (= c7bba3822_executed_after_significant_delay c7bba3822_executed_after_significant_delay))
(assert
 (= c7bba3822_slippage_only_protection c7bba3822_slippage_only_protection))
(assert
 (= c7bba3822_unwanted_trade_occurred c7bba3822_unwanted_trade_occurred))
(define-fun report_preconditions () Bool (and (not c7bba3822_deadline_param_supported)
     c7bba3822_slippage_only_protection))
(define-fun report_safety () Bool (=> (and (not c7bba3822_deadline_param_supported)
         c7bba3822_slippage_only_protection)
    (or (not c7bba3822_executed_after_significant_delay)
        (not c7bba3822_unwanted_trade_occurred))))
(define-fun report_effects () Bool (and (not c7bba3822_deadline_param_supported)
     c7bba3822_slippage_only_protection
     (not (or (not c7bba3822_executed_after_significant_delay)
              (not c7bba3822_unwanted_trade_occurred)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
