; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_invokes () Bool)
(declare-fun caller_is_authorized () Bool)
(declare-fun state_modified () Bool)
(assert
 (= caller_invokes caller_invokes))
(assert
 (= caller_is_authorized caller_is_authorized))
(assert
 (= state_modified state_modified))
(define-fun report_preconditions () Bool caller_invokes)
(define-fun report_safety () Bool (=> state_modified caller_is_authorized))
(define-fun report_effects () Bool (and (not caller_is_authorized) state_modified))
