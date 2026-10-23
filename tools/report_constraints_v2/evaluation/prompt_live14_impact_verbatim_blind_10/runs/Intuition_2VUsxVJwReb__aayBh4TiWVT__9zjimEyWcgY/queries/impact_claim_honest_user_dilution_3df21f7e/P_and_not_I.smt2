; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc7bb16fe_attacker_baseline_stake () Int)
(declare-fun cc7bb16fe_attacker_claim_boosted () Bool)
(declare-fun cc7bb16fe_boundary_deposit_offset () Int)
(declare-fun cc7bb16fe_claim_target_prev_epoch () Int)
(declare-fun cc7bb16fe_current_epoch_index () Int)
(declare-fun cc7bb16fe_honest_user_share_after () Int)
(declare-fun cc7bb16fe_honest_user_share_before () Int)
(assert
 (= cc7bb16fe_attacker_baseline_stake cc7bb16fe_attacker_baseline_stake))
(assert
 (= cc7bb16fe_attacker_claim_boosted cc7bb16fe_attacker_claim_boosted))
(assert
 (= cc7bb16fe_boundary_deposit_offset cc7bb16fe_boundary_deposit_offset))
(assert
 (= cc7bb16fe_claim_target_prev_epoch cc7bb16fe_claim_target_prev_epoch))
(assert
 (= cc7bb16fe_current_epoch_index cc7bb16fe_current_epoch_index))
(assert
 (= cc7bb16fe_honest_user_share_after cc7bb16fe_honest_user_share_after))
(assert
 (= cc7bb16fe_honest_user_share_before cc7bb16fe_honest_user_share_before))
(define-fun report_preconditions () Bool (and (< 0 cc7bb16fe_attacker_baseline_stake)
     (= 1 cc7bb16fe_boundary_deposit_offset)
     (= cc7bb16fe_claim_target_prev_epoch cc7bb16fe_current_epoch_index)))
(define-fun report_safety () Bool (=> (and (< 0 cc7bb16fe_attacker_baseline_stake)
         (= 1 cc7bb16fe_boundary_deposit_offset)
         (= cc7bb16fe_claim_target_prev_epoch cc7bb16fe_current_epoch_index))
    (and (not cc7bb16fe_attacker_claim_boosted)
         (>= cc7bb16fe_honest_user_share_after
             cc7bb16fe_honest_user_share_before))))
(define-fun report_effects () Bool (and (< 0 cc7bb16fe_attacker_baseline_stake)
     (= 1 cc7bb16fe_boundary_deposit_offset)
     (= cc7bb16fe_claim_target_prev_epoch cc7bb16fe_current_epoch_index)
     (not (and (not cc7bb16fe_attacker_claim_boosted)
               (>= cc7bb16fe_honest_user_share_after
                   cc7bb16fe_honest_user_share_before)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
