; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun recipient () ReportAddress)
(declare-fun zero_address () ReportAddress)
(declare-fun owner_after () ReportAddress)
(declare-fun caller_authorized () Bool)
(declare-fun locked_venft () Bool)
(assert
 (= recipient recipient))
(assert
 (= zero_address zero_address))
(assert
 (= owner_after owner_after))
(assert
 (= caller_authorized caller_authorized))
(assert
 (= locked_venft locked_venft))
(define-fun report_preconditions () Bool (and locked_venft (= recipient zero_address) caller_authorized))
(define-fun report_safety () Bool (=> (= recipient zero_address) (not (= owner_after zero_address))))
(define-fun report_effects () Bool (and (= recipient zero_address) (= owner_after zero_address)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
