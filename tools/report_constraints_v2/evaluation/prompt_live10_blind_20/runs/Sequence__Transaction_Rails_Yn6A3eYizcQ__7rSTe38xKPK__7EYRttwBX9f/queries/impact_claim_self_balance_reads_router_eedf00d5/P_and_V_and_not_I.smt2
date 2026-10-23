; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ced1f1961_balance_read_is_router () Bool)
(declare-fun ced1f1961_inject_and_call_available () Bool)
(assert
 (= ced1f1961_balance_read_is_router ced1f1961_balance_read_is_router))
(assert
 (= ced1f1961_inject_and_call_available ced1f1961_inject_and_call_available))
(define-fun report_preconditions () Bool ced1f1961_inject_and_call_available)
(define-fun report_safety () Bool (=> ced1f1961_inject_and_call_available (not ced1f1961_balance_read_is_router)))
(define-fun report_effects () Bool (and ced1f1961_inject_and_call_available
     (not (not ced1f1961_balance_read_is_router))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
