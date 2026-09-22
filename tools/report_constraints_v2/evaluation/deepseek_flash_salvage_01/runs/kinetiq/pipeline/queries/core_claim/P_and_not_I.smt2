; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun total_hype_before_slash () Int)
(declare-fun total_hype_after_slash () Int)
(declare-fun user1_withdrawal_amount () Int)
(declare-fun user2_withdrawal_amount () Int)
(declare-fun user1_confirmed_before_user2 () Bool)
(declare-fun user2_confirmation_succeeds () Bool)
(assert
 (= total_hype_before_slash total_hype_before_slash))
(assert
 (= total_hype_after_slash total_hype_after_slash))
(assert
 (= user1_withdrawal_amount user1_withdrawal_amount))
(assert
 (= user2_withdrawal_amount user2_withdrawal_amount))
(assert
 (= user1_confirmed_before_user2 user1_confirmed_before_user2))
(assert
 (= user2_confirmation_succeeds user2_confirmation_succeeds))
(define-fun report_preconditions () Bool (and (= 200 total_hype_before_slash)
     (= 100 user1_withdrawal_amount)
     (= 140 total_hype_after_slash)
     (= 70 user2_withdrawal_amount)
     user1_confirmed_before_user2))
(define-fun report_safety () Bool (=> user1_confirmed_before_user2 user2_confirmation_succeeds))
(define-fun report_effects () Bool (and user1_confirmed_before_user2 (not user2_confirmation_succeeds)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
