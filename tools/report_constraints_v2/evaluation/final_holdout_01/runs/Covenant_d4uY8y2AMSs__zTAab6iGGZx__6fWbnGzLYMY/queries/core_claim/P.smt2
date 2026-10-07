; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun sequencer_down () Bool)
(declare-fun quote_within_heartbeat () Bool)
(declare-fun sequencer_gate_present () Bool)
(declare-fun quote_accepted_for_valuation () Bool)
(assert
 (= sequencer_down sequencer_down))
(assert
 (= quote_within_heartbeat quote_within_heartbeat))
(assert
 (= sequencer_gate_present sequencer_gate_present))
(assert
 (= quote_accepted_for_valuation quote_accepted_for_valuation))
(define-fun report_preconditions () Bool (and sequencer_down quote_within_heartbeat (not sequencer_gate_present)))
(define-fun report_safety () Bool (=> (and sequencer_down quote_within_heartbeat (not sequencer_gate_present))
    (not quote_accepted_for_valuation)))
(define-fun report_effects () Bool (and sequencer_down
     quote_within_heartbeat
     (not sequencer_gate_present)
     (not (not quote_accepted_for_valuation))))
(assert report_preconditions)
(check-sat)
(get-model)
