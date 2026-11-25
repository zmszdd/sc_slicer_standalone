; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cac80ed30_interaction_with_non_market_prices_occurred () Bool)
(declare-fun cac80ed30_price_retrieval_occurred () Bool)
(declare-fun cac80ed30_protocol_on_l2 () Bool)
(declare-fun cac80ed30_sequencer_down () Bool)
(declare-fun cac80ed30_sequencer_uptime_checked () Bool)
(assert
 (= cac80ed30_interaction_with_non_market_prices_occurred cac80ed30_interaction_with_non_market_prices_occurred))
(assert
 (= cac80ed30_price_retrieval_occurred cac80ed30_price_retrieval_occurred))
(assert
 (= cac80ed30_protocol_on_l2 cac80ed30_protocol_on_l2))
(assert
 (= cac80ed30_sequencer_down cac80ed30_sequencer_down))
(assert
 (= cac80ed30_sequencer_uptime_checked cac80ed30_sequencer_uptime_checked))
(define-fun report_preconditions () Bool (and cac80ed30_protocol_on_l2 cac80ed30_sequencer_down))
(define-fun report_safety () Bool (=> cac80ed30_price_retrieval_occurred cac80ed30_sequencer_uptime_checked))
(define-fun report_effects () Bool (and cac80ed30_price_retrieval_occurred
     (not cac80ed30_sequencer_uptime_checked)
     cac80ed30_interaction_with_non_market_prices_occurred))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
