; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c918183db_attacker_baseline_stake () Int)
(declare-fun c918183db_boundary_deposit_offset () Int)
(declare-fun c918183db_boundary_utilization_credited () Int)
(declare-fun c918183db_claim_target_prev_epoch_offset () Int)
(declare-fun c918183db_emissions_extraction_pressure_observed () Bool)
(declare-fun c918183db_full_epoch_utilization_reference () Int)
(assert
 (= c918183db_attacker_baseline_stake c918183db_attacker_baseline_stake))
(assert
 (= c918183db_boundary_deposit_offset c918183db_boundary_deposit_offset))
(assert
 (= c918183db_boundary_utilization_credited c918183db_boundary_utilization_credited))
(assert
 (= c918183db_claim_target_prev_epoch_offset c918183db_claim_target_prev_epoch_offset))
(assert
 (= c918183db_emissions_extraction_pressure_observed c918183db_emissions_extraction_pressure_observed))
(assert
 (= c918183db_full_epoch_utilization_reference c918183db_full_epoch_utilization_reference))
(define-fun report_preconditions () Bool (and (< 0 c918183db_attacker_baseline_stake)
     (= 1 c918183db_boundary_deposit_offset)
     (= 1 c918183db_claim_target_prev_epoch_offset)))
(define-fun report_safety () Bool (=> (and (< 0 c918183db_attacker_baseline_stake)
         (= 1 c918183db_boundary_deposit_offset)
         (= 1 c918183db_claim_target_prev_epoch_offset))
    (or (<= c918183db_boundary_utilization_credited
            c918183db_full_epoch_utilization_reference)
        (not c918183db_emissions_extraction_pressure_observed))))
(define-fun report_effects () Bool (and (< 0 c918183db_attacker_baseline_stake)
     (= 1 c918183db_boundary_deposit_offset)
     (= 1 c918183db_claim_target_prev_epoch_offset)
     (not (or (<= c918183db_boundary_utilization_credited
                  c918183db_full_epoch_utilization_reference)
              (not c918183db_emissions_extraction_pressure_observed)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
