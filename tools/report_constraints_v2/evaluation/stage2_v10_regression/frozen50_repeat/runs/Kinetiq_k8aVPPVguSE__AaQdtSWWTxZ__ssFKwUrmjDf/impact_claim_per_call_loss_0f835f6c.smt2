; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd4ef94a1_caller_has_manager_role () Bool)
(declare-fun cd4ef94a1_cancelled_withdrawal_amount () Int)
(declare-fun cd4ef94a1_redelegation_lost_amount () Int)
(assert
 (= cd4ef94a1_caller_has_manager_role cd4ef94a1_caller_has_manager_role))
(assert
 (= cd4ef94a1_cancelled_withdrawal_amount cd4ef94a1_cancelled_withdrawal_amount))
(assert
 (= cd4ef94a1_redelegation_lost_amount cd4ef94a1_redelegation_lost_amount))
(define-fun report_preconditions () Bool (and (<= 0 cd4ef94a1_cancelled_withdrawal_amount)
     cd4ef94a1_caller_has_manager_role))
(define-fun report_safety () Bool (=> (and cd4ef94a1_caller_has_manager_role
         (<= 0 cd4ef94a1_cancelled_withdrawal_amount))
    (= 0 cd4ef94a1_redelegation_lost_amount)))
(define-fun report_effects () Bool (and cd4ef94a1_caller_has_manager_role
     (<= 0 cd4ef94a1_cancelled_withdrawal_amount)
     (not (= 0 cd4ef94a1_redelegation_lost_amount))))
