; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun lock_active () Bool)
(declare-fun caller () ReportAddress)
(declare-fun authorized_settler () ReportAddress)
(declare-fun debt_input_before () Int)
(declare-fun debt_input_after () Int)
(assert
 (= lock_active lock_active))
(assert
 (= caller caller))
(assert
 (= authorized_settler authorized_settler))
(assert
 (= debt_input_before debt_input_before))
(assert
 (= debt_input_after debt_input_after))
(define-fun report_preconditions () Bool (and lock_active (distinct caller authorized_settler) (< 0 debt_input_before)))
(define-fun report_safety () Bool (=> (< 0 debt_input_before) (not (= 0 debt_input_after))))
(define-fun report_effects () Bool (and (< 0 debt_input_before) (= 0 debt_input_after)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
