; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun owner_self_allowance_approved () Bool)
(declare-fun attacker_calls_withdraw () Bool)
(declare-fun caller_is_owner () Bool)
(declare-fun caller_has_valid_allowance () Bool)
(declare-fun unauthorized_withdrawal_occurred () Bool)
(assert
 (= owner_self_allowance_approved owner_self_allowance_approved))
(assert
 (= attacker_calls_withdraw attacker_calls_withdraw))
(assert
 (= caller_is_owner caller_is_owner))
(assert
 (= caller_has_valid_allowance caller_has_valid_allowance))
(assert
 (= unauthorized_withdrawal_occurred unauthorized_withdrawal_occurred))
(define-fun report_preconditions () Bool (and owner_self_allowance_approved attacker_calls_withdraw))
(define-fun report_safety () Bool (=> (and owner_self_allowance_approved attacker_calls_withdraw)
    (or caller_is_owner
        caller_has_valid_allowance
        (not unauthorized_withdrawal_occurred))))
(define-fun report_effects () Bool (and owner_self_allowance_approved
     attacker_calls_withdraw
     (not (or caller_is_owner
              caller_has_valid_allowance
              (not unauthorized_withdrawal_occurred)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
