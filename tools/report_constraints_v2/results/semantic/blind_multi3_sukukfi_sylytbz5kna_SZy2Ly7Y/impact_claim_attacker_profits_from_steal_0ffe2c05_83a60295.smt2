; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c67e5f524_attacker_steals_user_funds () Bool)
(declare-fun c67e5f524_caller_is_owner_or_operator () Bool)
(declare-fun c67e5f524_receiver_is_attacker () Bool)
(declare-fun c67e5f524_user_owns_withdrawable_shares () Bool)
(assert
 (= c67e5f524_attacker_steals_user_funds c67e5f524_attacker_steals_user_funds))
(assert
 (= c67e5f524_caller_is_owner_or_operator c67e5f524_caller_is_owner_or_operator))
(assert
 (= c67e5f524_receiver_is_attacker c67e5f524_receiver_is_attacker))
(assert
 (= c67e5f524_user_owns_withdrawable_shares c67e5f524_user_owns_withdrawable_shares))
(define-fun report_preconditions () Bool (and c67e5f524_user_owns_withdrawable_shares
     (not c67e5f524_caller_is_owner_or_operator)
     c67e5f524_receiver_is_attacker))
(define-fun report_safety () Bool (=> c67e5f524_user_owns_withdrawable_shares
    c67e5f524_caller_is_owner_or_operator))
(define-fun report_effects () Bool c67e5f524_attacker_steals_user_funds)
