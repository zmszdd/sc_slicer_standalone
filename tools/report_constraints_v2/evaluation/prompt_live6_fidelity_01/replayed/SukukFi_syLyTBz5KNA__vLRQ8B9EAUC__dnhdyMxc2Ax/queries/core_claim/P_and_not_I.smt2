; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun supports_interface_implemented () Bool)
(declare-fun eip7575_interface_check_returns_true () Bool)
(assert
 (= supports_interface_implemented supports_interface_implemented))
(assert
 (= eip7575_interface_check_returns_true eip7575_interface_check_returns_true))
(define-fun report_preconditions () Bool supports_interface_implemented)
(define-fun report_safety () Bool (=> supports_interface_implemented eip7575_interface_check_returns_true))
(define-fun report_effects () Bool (and supports_interface_implemented (not eip7575_interface_check_returns_true)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
