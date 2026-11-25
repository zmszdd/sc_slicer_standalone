; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c49c0921e_deployed_on_l2_with_centralized_sequencer () Bool)
(declare-fun c49c0921e_loss_of_funds_from_corrupted_price_trades () Bool)
(declare-fun c49c0921e_sequencer_downtime_occurs () Bool)
(declare-fun c49c0921e_sequencer_restart_backlog () Bool)
(declare-fun c49c0921e_sequencer_uptime_validated_before_snapshot () Bool)
(declare-fun c49c0921e_snapshot_recorded () Bool)
(declare-fun c49c0921e_timestamp_frozen_during_downtime () Bool)
(assert
 (= c49c0921e_deployed_on_l2_with_centralized_sequencer c49c0921e_deployed_on_l2_with_centralized_sequencer))
(assert
 (= c49c0921e_loss_of_funds_from_corrupted_price_trades c49c0921e_loss_of_funds_from_corrupted_price_trades))
(assert
 (= c49c0921e_sequencer_downtime_occurs c49c0921e_sequencer_downtime_occurs))
(assert
 (= c49c0921e_sequencer_restart_backlog c49c0921e_sequencer_restart_backlog))
(assert
 (= c49c0921e_sequencer_uptime_validated_before_snapshot c49c0921e_sequencer_uptime_validated_before_snapshot))
(assert
 (= c49c0921e_snapshot_recorded c49c0921e_snapshot_recorded))
(assert
 (= c49c0921e_timestamp_frozen_during_downtime c49c0921e_timestamp_frozen_during_downtime))
(define-fun report_preconditions () Bool (and c49c0921e_deployed_on_l2_with_centralized_sequencer
     c49c0921e_sequencer_downtime_occurs
     c49c0921e_timestamp_frozen_during_downtime
     c49c0921e_sequencer_restart_backlog))
(define-fun report_safety () Bool (=> (and c49c0921e_deployed_on_l2_with_centralized_sequencer
         c49c0921e_snapshot_recorded)
    c49c0921e_sequencer_uptime_validated_before_snapshot))
(define-fun report_effects () Bool (and c49c0921e_deployed_on_l2_with_centralized_sequencer
     c49c0921e_snapshot_recorded
     (not c49c0921e_sequencer_uptime_validated_before_snapshot)
     c49c0921e_loss_of_funds_from_corrupted_price_trades))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
