; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c139e47f2_end_rewards_accrual_unavailable_before () Bool)
(declare-fun c139e47f2_fee_share_decrease_occurred () Bool)
(declare-fun c139e47f2_pair_core_operation_completed () Bool)
(declare-fun c139e47f2_total_fee_share_before () Int)
(declare-fun c139e47f2_unlocked_before () Bool)
(assert
 (= c139e47f2_end_rewards_accrual_unavailable_before c139e47f2_end_rewards_accrual_unavailable_before))
(assert
 (= c139e47f2_fee_share_decrease_occurred c139e47f2_fee_share_decrease_occurred))
(assert
 (= c139e47f2_pair_core_operation_completed c139e47f2_pair_core_operation_completed))
(assert
 (= c139e47f2_total_fee_share_before c139e47f2_total_fee_share_before))
(assert
 (= c139e47f2_unlocked_before c139e47f2_unlocked_before))
(define-fun report_preconditions () Bool (and c139e47f2_unlocked_before
     c139e47f2_fee_share_decrease_occurred
     (= 0 c139e47f2_total_fee_share_before)
     c139e47f2_end_rewards_accrual_unavailable_before))
(define-fun report_safety () Bool (=> (and c139e47f2_unlocked_before
         c139e47f2_fee_share_decrease_occurred
         (= 0 c139e47f2_total_fee_share_before)
         c139e47f2_end_rewards_accrual_unavailable_before)
    c139e47f2_pair_core_operation_completed))
(define-fun report_effects () Bool (and c139e47f2_unlocked_before
     c139e47f2_fee_share_decrease_occurred
     (= 0 c139e47f2_total_fee_share_before)
     c139e47f2_end_rewards_accrual_unavailable_before
     (not c139e47f2_pair_core_operation_completed)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
