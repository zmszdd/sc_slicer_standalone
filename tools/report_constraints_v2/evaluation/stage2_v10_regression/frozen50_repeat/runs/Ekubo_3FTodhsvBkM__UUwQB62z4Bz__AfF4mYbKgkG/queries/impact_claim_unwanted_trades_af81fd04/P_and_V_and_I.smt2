; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c832f7903_market_conditions_changed () Bool)
(declare-fun c832f7903_swap_submitted_without_deadline () Bool)
(declare-fun c832f7903_tx_delayed_in_mempool () Bool)
(declare-fun c832f7903_unwanted_trade_occurred () Bool)
(assert
 (= c832f7903_market_conditions_changed c832f7903_market_conditions_changed))
(assert
 (= c832f7903_swap_submitted_without_deadline c832f7903_swap_submitted_without_deadline))
(assert
 (= c832f7903_tx_delayed_in_mempool c832f7903_tx_delayed_in_mempool))
(assert
 (= c832f7903_unwanted_trade_occurred c832f7903_unwanted_trade_occurred))
(define-fun report_preconditions () Bool (and c832f7903_swap_submitted_without_deadline
     c832f7903_tx_delayed_in_mempool
     c832f7903_market_conditions_changed))
(define-fun report_safety () Bool (=> (and c832f7903_swap_submitted_without_deadline
         c832f7903_tx_delayed_in_mempool
         c832f7903_market_conditions_changed)
    (not c832f7903_unwanted_trade_occurred)))
(define-fun report_effects () Bool (and c832f7903_swap_submitted_without_deadline
     c832f7903_tx_delayed_in_mempool
     c832f7903_market_conditions_changed
     (not (not c832f7903_unwanted_trade_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
