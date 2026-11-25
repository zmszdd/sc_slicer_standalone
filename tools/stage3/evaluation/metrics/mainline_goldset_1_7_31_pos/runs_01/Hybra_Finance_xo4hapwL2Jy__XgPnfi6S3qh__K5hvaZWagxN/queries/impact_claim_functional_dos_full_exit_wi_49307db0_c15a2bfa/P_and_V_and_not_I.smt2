; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3c23aaf6_full_exit_withdrawal_completes () Bool)
(declare-fun c3c23aaf6_full_exit_withdrawal_reverts () Bool)
(declare-fun c3c23aaf6_remaining_amount () Int)
(declare-fun c3c23aaf6_split_allowed_ghybr () Bool)
(declare-fun c3c23aaf6_user_withdraws_all_shares () Bool)
(assert
 (= c3c23aaf6_full_exit_withdrawal_completes c3c23aaf6_full_exit_withdrawal_completes))
(assert
 (= c3c23aaf6_full_exit_withdrawal_reverts c3c23aaf6_full_exit_withdrawal_reverts))
(assert
 (= c3c23aaf6_remaining_amount c3c23aaf6_remaining_amount))
(assert
 (= c3c23aaf6_split_allowed_ghybr c3c23aaf6_split_allowed_ghybr))
(assert
 (= c3c23aaf6_user_withdraws_all_shares c3c23aaf6_user_withdraws_all_shares))
(define-fun report_preconditions () Bool (and c3c23aaf6_user_withdraws_all_shares
     (= 0 c3c23aaf6_remaining_amount)
     c3c23aaf6_split_allowed_ghybr))
(define-fun report_safety () Bool (=> (and c3c23aaf6_user_withdraws_all_shares (= 0 c3c23aaf6_remaining_amount))
    c3c23aaf6_full_exit_withdrawal_completes))
(define-fun report_effects () Bool (and c3c23aaf6_user_withdraws_all_shares
     (= 0 c3c23aaf6_remaining_amount)
     (not c3c23aaf6_full_exit_withdrawal_completes)
     c3c23aaf6_full_exit_withdrawal_reverts))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
