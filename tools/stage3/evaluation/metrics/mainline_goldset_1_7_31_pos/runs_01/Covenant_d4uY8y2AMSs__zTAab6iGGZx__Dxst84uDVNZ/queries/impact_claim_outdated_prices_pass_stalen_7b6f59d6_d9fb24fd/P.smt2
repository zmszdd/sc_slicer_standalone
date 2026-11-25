; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c99470901_price_retrieval_prevented () Bool)
(declare-fun c99470901_prices_outdated () Bool)
(declare-fun c99470901_prices_pass_staleness_checks () Bool)
(declare-fun c99470901_protocol_on_l2 () Bool)
(declare-fun c99470901_sequencer_downtime_occurred () Bool)
(declare-fun c99470901_sequencer_restarted () Bool)
(assert
 (= c99470901_price_retrieval_prevented c99470901_price_retrieval_prevented))
(assert
 (= c99470901_prices_outdated c99470901_prices_outdated))
(assert
 (= c99470901_prices_pass_staleness_checks c99470901_prices_pass_staleness_checks))
(assert
 (= c99470901_protocol_on_l2 c99470901_protocol_on_l2))
(assert
 (= c99470901_sequencer_downtime_occurred c99470901_sequencer_downtime_occurred))
(assert
 (= c99470901_sequencer_restarted c99470901_sequencer_restarted))
(define-fun report_preconditions () Bool (and c99470901_protocol_on_l2
     c99470901_sequencer_downtime_occurred
     c99470901_sequencer_restarted))
(define-fun report_safety () Bool (=> (and c99470901_protocol_on_l2
         c99470901_sequencer_downtime_occurred
         c99470901_sequencer_restarted)
    c99470901_price_retrieval_prevented))
(define-fun report_effects () Bool (and c99470901_protocol_on_l2
     c99470901_sequencer_downtime_occurred
     c99470901_sequencer_restarted
     (not c99470901_price_retrieval_prevented)
     c99470901_prices_pass_staleness_checks
     c99470901_prices_outdated
     c99470901_sequencer_restarted))
(assert report_preconditions)
(check-sat)
(get-model)
