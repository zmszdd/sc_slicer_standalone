; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf0a9d719_attacker_has_baseline_stake () Bool)
(declare-fun cf0a9d719_boundary_boost_exceeds_held_epoch_claim () Bool)
(declare-fun cf0a9d719_claim_targets_prev_epoch_e () Bool)
(declare-fun cf0a9d719_deposit_at_boundary_minus_one () Bool)
(assert
 (= cf0a9d719_attacker_has_baseline_stake cf0a9d719_attacker_has_baseline_stake))
(assert
 (= cf0a9d719_boundary_boost_exceeds_held_epoch_claim cf0a9d719_boundary_boost_exceeds_held_epoch_claim))
(assert
 (= cf0a9d719_claim_targets_prev_epoch_e cf0a9d719_claim_targets_prev_epoch_e))
(assert
 (= cf0a9d719_deposit_at_boundary_minus_one cf0a9d719_deposit_at_boundary_minus_one))
(define-fun report_preconditions () Bool (and cf0a9d719_attacker_has_baseline_stake
     cf0a9d719_deposit_at_boundary_minus_one
     cf0a9d719_claim_targets_prev_epoch_e))
(define-fun report_safety () Bool (=> (and cf0a9d719_attacker_has_baseline_stake
         cf0a9d719_deposit_at_boundary_minus_one
         cf0a9d719_claim_targets_prev_epoch_e)
    (not cf0a9d719_boundary_boost_exceeds_held_epoch_claim)))
(define-fun report_effects () Bool (and cf0a9d719_attacker_has_baseline_stake
     cf0a9d719_deposit_at_boundary_minus_one
     cf0a9d719_claim_targets_prev_epoch_e
     (not (not cf0a9d719_boundary_boost_exceeds_held_epoch_claim))))
(assert report_preconditions)
(check-sat)
(get-model)
