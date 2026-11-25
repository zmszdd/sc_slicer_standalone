; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4b2fab19_backlog_executes_with_stale_timestamp () Bool)
(declare-fun c4b2fab19_block_timestamp_frozen () Bool)
(declare-fun c4b2fab19_downtime_detection_mechanism_present () Bool)
(declare-fun c4b2fab19_l2_has_centralized_sequencer () Bool)
(declare-fun c4b2fab19_price_manipulation_via_downtime_window () Bool)
(declare-fun c4b2fab19_sequencer_downtime_occurred () Bool)
(declare-fun c4b2fab19_snapshot_recorded_from_stale_timestamp () Bool)
(assert
 (= c4b2fab19_backlog_executes_with_stale_timestamp c4b2fab19_backlog_executes_with_stale_timestamp))
(assert
 (= c4b2fab19_block_timestamp_frozen c4b2fab19_block_timestamp_frozen))
(assert
 (= c4b2fab19_downtime_detection_mechanism_present c4b2fab19_downtime_detection_mechanism_present))
(assert
 (= c4b2fab19_l2_has_centralized_sequencer c4b2fab19_l2_has_centralized_sequencer))
(assert
 (= c4b2fab19_price_manipulation_via_downtime_window c4b2fab19_price_manipulation_via_downtime_window))
(assert
 (= c4b2fab19_sequencer_downtime_occurred c4b2fab19_sequencer_downtime_occurred))
(assert
 (= c4b2fab19_snapshot_recorded_from_stale_timestamp c4b2fab19_snapshot_recorded_from_stale_timestamp))
(define-fun report_preconditions () Bool (and c4b2fab19_l2_has_centralized_sequencer
     c4b2fab19_sequencer_downtime_occurred
     c4b2fab19_block_timestamp_frozen
     c4b2fab19_backlog_executes_with_stale_timestamp
     c4b2fab19_downtime_detection_mechanism_present))
(define-fun report_safety () Bool (= c4b2fab19_snapshot_recorded_from_stale_timestamp
   c4b2fab19_downtime_detection_mechanism_present))
(define-fun report_effects () Bool (and c4b2fab19_downtime_detection_mechanism_present
     (not (= c4b2fab19_snapshot_recorded_from_stale_timestamp
             c4b2fab19_downtime_detection_mechanism_present))
     c4b2fab19_price_manipulation_via_downtime_window))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
