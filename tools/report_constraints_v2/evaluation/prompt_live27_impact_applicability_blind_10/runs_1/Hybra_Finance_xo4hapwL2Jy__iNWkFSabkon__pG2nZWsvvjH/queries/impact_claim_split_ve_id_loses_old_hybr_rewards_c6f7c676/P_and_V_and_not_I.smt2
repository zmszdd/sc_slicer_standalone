; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf1034739_claim_rewards_not_called_before_withdrawal () Bool)
(declare-fun cf1034739_ghybr_holds_ve_with_earned_rewards () Bool)
(declare-fun cf1034739_ghybr_old_ve_hybr_rewards_after_split () Int)
(declare-fun cf1034739_ghybr_old_ve_hybr_rewards_before_split () Int)
(declare-fun cf1034739_ghybr_ve_id_split_during_withdrawal () Bool)
(assert
 (= cf1034739_claim_rewards_not_called_before_withdrawal cf1034739_claim_rewards_not_called_before_withdrawal))
(assert
 (= cf1034739_ghybr_holds_ve_with_earned_rewards cf1034739_ghybr_holds_ve_with_earned_rewards))
(assert
 (= cf1034739_ghybr_old_ve_hybr_rewards_after_split cf1034739_ghybr_old_ve_hybr_rewards_after_split))
(assert
 (= cf1034739_ghybr_old_ve_hybr_rewards_before_split cf1034739_ghybr_old_ve_hybr_rewards_before_split))
(assert
 (= cf1034739_ghybr_ve_id_split_during_withdrawal cf1034739_ghybr_ve_id_split_during_withdrawal))
(define-fun report_preconditions () Bool (and cf1034739_ghybr_holds_ve_with_earned_rewards
     cf1034739_claim_rewards_not_called_before_withdrawal))
(define-fun report_safety () Bool (=> cf1034739_ghybr_ve_id_split_during_withdrawal
    (=> cf1034739_ghybr_ve_id_split_during_withdrawal
        (= cf1034739_ghybr_old_ve_hybr_rewards_after_split
           cf1034739_ghybr_old_ve_hybr_rewards_before_split))))
(define-fun report_effects () Bool (and cf1034739_ghybr_ve_id_split_during_withdrawal
     cf1034739_ghybr_ve_id_split_during_withdrawal
     (not (= cf1034739_ghybr_old_ve_hybr_rewards_after_split
             cf1034739_ghybr_old_ve_hybr_rewards_before_split))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
