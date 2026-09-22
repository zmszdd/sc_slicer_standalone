; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun swap_submitted () Bool)
(declare-fun swap_pending () Bool)
(declare-fun gas_prices_dropped () Bool)
(declare-fun execution_time () Int)
(declare-fun deadline () Int)
(declare-fun trade_after_intent_change () Bool)
(assert
 (= swap_submitted swap_submitted))
(assert
 (= swap_pending swap_pending))
(assert
 (= gas_prices_dropped gas_prices_dropped))
(assert
 (= execution_time execution_time))
(assert
 (= deadline deadline))
(assert
 (= trade_after_intent_change trade_after_intent_change))
(define-fun report_preconditions () Bool (and swap_submitted swap_pending gas_prices_dropped))
(define-fun report_safety () Bool (=> (and swap_submitted
         swap_pending
         gas_prices_dropped
         (> execution_time deadline))
    (not trade_after_intent_change)))
(define-fun report_effects () Bool (and swap_submitted
     swap_pending
     gas_prices_dropped
     (> execution_time deadline)
     trade_after_intent_change))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
