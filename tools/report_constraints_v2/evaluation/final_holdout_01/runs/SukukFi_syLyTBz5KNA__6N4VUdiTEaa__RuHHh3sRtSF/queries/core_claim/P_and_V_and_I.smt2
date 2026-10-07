; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun contract_paused () Bool)
(declare-fun privileged_flow_invoked () Bool)
(declare-fun must_not_be_paused_requirement () Bool)
(declare-fun funds_moved () Bool)
(assert
 (= contract_paused contract_paused))
(assert
 (= privileged_flow_invoked privileged_flow_invoked))
(assert
 (= must_not_be_paused_requirement must_not_be_paused_requirement))
(assert
 (= funds_moved funds_moved))
(define-fun report_preconditions () Bool (and contract_paused privileged_flow_invoked must_not_be_paused_requirement))
(define-fun report_safety () Bool (=> (and contract_paused privileged_flow_invoked must_not_be_paused_requirement)
    (not funds_moved)))
(define-fun report_effects () Bool (and contract_paused
     privileged_flow_invoked
     must_not_be_paused_requirement
     (not (not funds_moved))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
