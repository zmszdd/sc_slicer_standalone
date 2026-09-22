; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun owner () ReportAddress)
(declare-fun caller () ReportAddress)
(declare-fun owner_configured () Bool)
(declare-fun withdrawal_completed () Bool)
(assert
 (= owner owner))
(assert
 (= caller caller))
(assert
 (= owner_configured owner_configured))
(assert
 (= withdrawal_completed withdrawal_completed))
(define-fun report_preconditions () Bool (and owner_configured (distinct caller owner)))
(define-fun report_safety () Bool (=> withdrawal_completed (= caller owner)))
(define-fun report_effects () Bool (and withdrawal_completed (not (= caller owner))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
