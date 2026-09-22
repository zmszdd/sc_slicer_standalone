; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun victim_deposited () Bool)
(declare-fun has_self_allowance () Bool)
(declare-fun accepts_arbitrary_owner () Bool)
(declare-fun only_self_allowance_checked () Bool)
(declare-fun any_caller_can_call () Bool)
(declare-fun caller_is_owner () Bool)
(declare-fun owner_position_spent () Bool)
(declare-fun caller_authorized () Bool)
(assert
 (= victim_deposited victim_deposited))
(assert
 (= has_self_allowance has_self_allowance))
(assert
 (= accepts_arbitrary_owner accepts_arbitrary_owner))
(assert
 (= only_self_allowance_checked only_self_allowance_checked))
(assert
 (= any_caller_can_call any_caller_can_call))
(assert
 (= caller_is_owner caller_is_owner))
(assert
 (= owner_position_spent owner_position_spent))
(assert
 (= caller_authorized caller_authorized))
(define-fun report_preconditions () Bool (and victim_deposited
     has_self_allowance
     accepts_arbitrary_owner
     only_self_allowance_checked
     any_caller_can_call
     (not caller_is_owner)))
(define-fun report_safety () Bool (=> (and (not caller_is_owner) owner_position_spent) caller_authorized))
(define-fun report_effects () Bool (and owner_position_spent (not caller_authorized)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
