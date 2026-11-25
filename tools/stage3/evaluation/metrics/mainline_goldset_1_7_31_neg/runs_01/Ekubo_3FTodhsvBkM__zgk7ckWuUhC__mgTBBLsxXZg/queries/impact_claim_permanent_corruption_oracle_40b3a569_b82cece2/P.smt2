; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44b29451_l2_with_centralized_sequencer () Bool)
(declare-fun c44b29451_oracle_data_permanently_corrupted () Bool)
(declare-fun c44b29451_sequencer_downtime_occurs () Bool)
(declare-fun c44b29451_sequencer_restart_backlog () Bool)
(declare-fun c44b29451_sequencer_uptime_validated_before_snapshot () Bool)
(declare-fun c44b29451_snapshot_recorded () Bool)
(declare-fun c44b29451_timestamp_frozen_during_downtime () Bool)
(assert
 (= c44b29451_l2_with_centralized_sequencer c44b29451_l2_with_centralized_sequencer))
(assert
 (= c44b29451_oracle_data_permanently_corrupted c44b29451_oracle_data_permanently_corrupted))
(assert
 (= c44b29451_sequencer_downtime_occurs c44b29451_sequencer_downtime_occurs))
(assert
 (= c44b29451_sequencer_restart_backlog c44b29451_sequencer_restart_backlog))
(assert
 (= c44b29451_sequencer_uptime_validated_before_snapshot c44b29451_sequencer_uptime_validated_before_snapshot))
(assert
 (= c44b29451_snapshot_recorded c44b29451_snapshot_recorded))
(assert
 (= c44b29451_timestamp_frozen_during_downtime c44b29451_timestamp_frozen_during_downtime))
(define-fun report_preconditions () Bool (and c44b29451_l2_with_centralized_sequencer
     c44b29451_sequencer_downtime_occurs
     c44b29451_timestamp_frozen_during_downtime
     c44b29451_sequencer_restart_backlog))
(define-fun report_safety () Bool (=> (and c44b29451_l2_with_centralized_sequencer c44b29451_snapshot_recorded)
    c44b29451_sequencer_uptime_validated_before_snapshot))
(define-fun report_effects () Bool (and c44b29451_l2_with_centralized_sequencer
     c44b29451_snapshot_recorded
     (not c44b29451_sequencer_uptime_validated_before_snapshot)
     c44b29451_oracle_data_permanently_corrupted
     c44b29451_oracle_data_permanently_corrupted))
(assert report_preconditions)
(check-sat)
(get-model)
