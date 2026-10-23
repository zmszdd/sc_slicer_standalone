; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd462abb9_user_entered_cooldown () Bool)
(declare-fun cd462abb9_user_has_full_restricted_staker_role () Bool)
(declare-fun cd462abb9_withdrawal_succeeded () Bool)
(assert
 (= cd462abb9_user_entered_cooldown cd462abb9_user_entered_cooldown))
(assert
 (= cd462abb9_user_has_full_restricted_staker_role cd462abb9_user_has_full_restricted_staker_role))
(assert
 (= cd462abb9_withdrawal_succeeded cd462abb9_withdrawal_succeeded))
(define-fun report_preconditions () Bool (and cd462abb9_user_entered_cooldown
     cd462abb9_user_has_full_restricted_staker_role))
(define-fun report_safety () Bool (=> (and cd462abb9_user_entered_cooldown
         cd462abb9_user_has_full_restricted_staker_role)
    (not cd462abb9_withdrawal_succeeded)))
(define-fun report_effects () Bool (and cd462abb9_user_entered_cooldown
     cd462abb9_user_has_full_restricted_staker_role
     (not (not cd462abb9_withdrawal_succeeded))))
(assert report_preconditions)
(check-sat)
(get-model)
