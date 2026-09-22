; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun fees_accumulated () Bool)
(declare-fun builderadmin_guards_sweep () Bool)
(declare-fun builderadmin_overwritten () Bool)
(declare-fun sweep_called () Bool)
(declare-fun sweep_caller () ReportAddress)
(declare-fun legitimate_builderadmin () ReportAddress)
(declare-fun fees_stolen () Bool)
(assert
 (= fees_accumulated fees_accumulated))
(assert
 (= builderadmin_guards_sweep builderadmin_guards_sweep))
(assert
 (= builderadmin_overwritten builderadmin_overwritten))
(assert
 (= sweep_called sweep_called))
(assert
 (= sweep_caller sweep_caller))
(assert
 (= legitimate_builderadmin legitimate_builderadmin))
(assert
 (= fees_stolen fees_stolen))
(define-fun report_preconditions () Bool (and fees_accumulated builderadmin_guards_sweep))
(define-fun report_safety () Bool (and (not builderadmin_overwritten)
     (=> sweep_called (= sweep_caller legitimate_builderadmin))))
(define-fun report_effects () Bool fees_stolen)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
