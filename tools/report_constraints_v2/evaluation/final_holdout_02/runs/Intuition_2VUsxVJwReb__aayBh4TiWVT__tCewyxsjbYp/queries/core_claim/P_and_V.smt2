; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun snapshot_lookup_inclusive () Bool)
(declare-fun epoch_end_snapshot_used () Bool)
(declare-fun lock_at_boundary () Bool)
(declare-fun no_epoch_cap_guard () Bool)
(declare-fun total_claimed_rewards () Int)
(declare-fun epoch_emissions () Int)
(assert
 (= snapshot_lookup_inclusive snapshot_lookup_inclusive))
(assert
 (= epoch_end_snapshot_used epoch_end_snapshot_used))
(assert
 (= lock_at_boundary lock_at_boundary))
(assert
 (= no_epoch_cap_guard no_epoch_cap_guard))
(assert
 (= total_claimed_rewards total_claimed_rewards))
(assert
 (= epoch_emissions epoch_emissions))
(define-fun report_preconditions () Bool (and snapshot_lookup_inclusive
     epoch_end_snapshot_used
     lock_at_boundary
     no_epoch_cap_guard))
(define-fun report_safety () Bool (=> (and snapshot_lookup_inclusive
         epoch_end_snapshot_used
         lock_at_boundary
         no_epoch_cap_guard)
    (<= total_claimed_rewards epoch_emissions)))
(define-fun report_effects () Bool (and snapshot_lookup_inclusive
     epoch_end_snapshot_used
     lock_at_boundary
     no_epoch_cap_guard
     (not (<= total_claimed_rewards epoch_emissions))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
