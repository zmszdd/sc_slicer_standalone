; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c45628529_backlog_executes_with_stale_timestamp () Bool)
(declare-fun c45628529_block_timestamp_frozen () Bool)
(declare-fun c45628529_downtime_detection_mechanism_present () Bool)
(declare-fun c45628529_l2_has_centralized_sequencer () Bool)
(declare-fun c45628529_oracle_data_permanently_corrupted () Bool)
(declare-fun c45628529_sequencer_downtime_occurred () Bool)
(declare-fun c45628529_snapshot_recorded_from_stale_timestamp () Bool)
(assert
 (= c45628529_backlog_executes_with_stale_timestamp c45628529_backlog_executes_with_stale_timestamp))
(assert
 (= c45628529_block_timestamp_frozen c45628529_block_timestamp_frozen))
(assert
 (= c45628529_downtime_detection_mechanism_present c45628529_downtime_detection_mechanism_present))
(assert
 (= c45628529_l2_has_centralized_sequencer c45628529_l2_has_centralized_sequencer))
(assert
 (= c45628529_oracle_data_permanently_corrupted c45628529_oracle_data_permanently_corrupted))
(assert
 (= c45628529_sequencer_downtime_occurred c45628529_sequencer_downtime_occurred))
(assert
 (= c45628529_snapshot_recorded_from_stale_timestamp c45628529_snapshot_recorded_from_stale_timestamp))
(define-fun report_preconditions () Bool (and c45628529_l2_has_centralized_sequencer
     c45628529_sequencer_downtime_occurred
     c45628529_block_timestamp_frozen
     c45628529_backlog_executes_with_stale_timestamp))
(define-fun report_safety () Bool (=> c45628529_l2_has_centralized_sequencer
    (= c45628529_downtime_detection_mechanism_present
       c45628529_snapshot_recorded_from_stale_timestamp)))
(define-fun report_effects () Bool (and c45628529_l2_has_centralized_sequencer
     (not (= c45628529_downtime_detection_mechanism_present
             c45628529_snapshot_recorded_from_stale_timestamp))
     c45628529_oracle_data_permanently_corrupted
     c45628529_oracle_data_permanently_corrupted))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
