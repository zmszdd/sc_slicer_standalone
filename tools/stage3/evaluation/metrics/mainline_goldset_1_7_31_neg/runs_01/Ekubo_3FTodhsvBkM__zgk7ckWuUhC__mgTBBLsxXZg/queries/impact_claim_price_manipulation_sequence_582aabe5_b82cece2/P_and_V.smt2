; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c13eb2035_backlog_executes_with_stale_timestamp () Bool)
(declare-fun c13eb2035_block_timestamp_frozen_during_downtime () Bool)
(declare-fun c13eb2035_l2_centralized_sequencer_deployment () Bool)
(declare-fun c13eb2035_price_manipulation_via_downtime_window () Bool)
(declare-fun c13eb2035_sequencer_downtime_occurred () Bool)
(declare-fun c13eb2035_sequencer_uptime_validated_before_snapshot () Bool)
(declare-fun c13eb2035_snapshot_recorded () Bool)
(assert
 (= c13eb2035_backlog_executes_with_stale_timestamp c13eb2035_backlog_executes_with_stale_timestamp))
(assert
 (= c13eb2035_block_timestamp_frozen_during_downtime c13eb2035_block_timestamp_frozen_during_downtime))
(assert
 (= c13eb2035_l2_centralized_sequencer_deployment c13eb2035_l2_centralized_sequencer_deployment))
(assert
 (= c13eb2035_price_manipulation_via_downtime_window c13eb2035_price_manipulation_via_downtime_window))
(assert
 (= c13eb2035_sequencer_downtime_occurred c13eb2035_sequencer_downtime_occurred))
(assert
 (= c13eb2035_sequencer_uptime_validated_before_snapshot c13eb2035_sequencer_uptime_validated_before_snapshot))
(assert
 (= c13eb2035_snapshot_recorded c13eb2035_snapshot_recorded))
(define-fun report_preconditions () Bool (and c13eb2035_l2_centralized_sequencer_deployment
     c13eb2035_sequencer_downtime_occurred
     c13eb2035_block_timestamp_frozen_during_downtime
     c13eb2035_backlog_executes_with_stale_timestamp))
(define-fun report_safety () Bool (=> (and c13eb2035_l2_centralized_sequencer_deployment
         c13eb2035_snapshot_recorded)
    c13eb2035_sequencer_uptime_validated_before_snapshot))
(define-fun report_effects () Bool (and c13eb2035_l2_centralized_sequencer_deployment
     c13eb2035_snapshot_recorded
     (not c13eb2035_sequencer_uptime_validated_before_snapshot)
     c13eb2035_price_manipulation_via_downtime_window))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
