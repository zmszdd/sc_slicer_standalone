; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun epoch_duration_seconds () Int)
(declare-fun attacker_prior_epoch_position () Int)
(declare-fun snapshot_balance_weight () Int)
(declare-fun duration_weighted_share_denominator () Int)
(declare-fun attacker_contribution_seconds () Int)
(declare-fun utilization_ratio_duration_blind () Bool)
(assert
 (= epoch_duration_seconds epoch_duration_seconds))
(assert
 (= attacker_prior_epoch_position attacker_prior_epoch_position))
(assert
 (= snapshot_balance_weight snapshot_balance_weight))
(assert
 (= duration_weighted_share_denominator duration_weighted_share_denominator))
(assert
 (= attacker_contribution_seconds attacker_contribution_seconds))
(assert
 (= utilization_ratio_duration_blind utilization_ratio_duration_blind))
(define-fun report_preconditions () Bool (and (= 1209600 epoch_duration_seconds)
     (= 0 attacker_prior_epoch_position)
     utilization_ratio_duration_blind
     utilization_ratio_duration_blind))
(define-fun report_safety () Bool (=> (= duration_weighted_share_denominator epoch_duration_seconds)
    (=> (and (= 1209600 epoch_duration_seconds)
             (= 0 attacker_prior_epoch_position)
             utilization_ratio_duration_blind)
        (<= (* snapshot_balance_weight attacker_contribution_seconds)
            (* snapshot_balance_weight duration_weighted_share_denominator)))))
(define-fun report_effects () Bool (and (= duration_weighted_share_denominator epoch_duration_seconds)
     (= 1209600 epoch_duration_seconds)
     (= 0 attacker_prior_epoch_position)
     utilization_ratio_duration_blind
     (not (<= (* snapshot_balance_weight attacker_contribution_seconds)
              (* snapshot_balance_weight duration_weighted_share_denominator)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
