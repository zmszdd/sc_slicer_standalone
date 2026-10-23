; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7e6b4d3a_executed_after_significant_delay () Bool)
(declare-fun c7e6b4d3a_market_conditions_changed () Bool)
(declare-fun c7e6b4d3a_swap_submitted_without_deadline () Bool)
(declare-fun c7e6b4d3a_tx_delayed_in_mempool () Bool)
(assert
 (= c7e6b4d3a_executed_after_significant_delay c7e6b4d3a_executed_after_significant_delay))
(assert
 (= c7e6b4d3a_market_conditions_changed c7e6b4d3a_market_conditions_changed))
(assert
 (= c7e6b4d3a_swap_submitted_without_deadline c7e6b4d3a_swap_submitted_without_deadline))
(assert
 (= c7e6b4d3a_tx_delayed_in_mempool c7e6b4d3a_tx_delayed_in_mempool))
(define-fun report_preconditions () Bool (and c7e6b4d3a_swap_submitted_without_deadline
     c7e6b4d3a_tx_delayed_in_mempool
     c7e6b4d3a_market_conditions_changed))
(define-fun report_safety () Bool (=> (and c7e6b4d3a_swap_submitted_without_deadline
         c7e6b4d3a_tx_delayed_in_mempool
         c7e6b4d3a_market_conditions_changed)
    (not c7e6b4d3a_executed_after_significant_delay)))
(define-fun report_effects () Bool (and c7e6b4d3a_swap_submitted_without_deadline
     c7e6b4d3a_tx_delayed_in_mempool
     c7e6b4d3a_market_conditions_changed
     (not (not c7e6b4d3a_executed_after_significant_delay))))
