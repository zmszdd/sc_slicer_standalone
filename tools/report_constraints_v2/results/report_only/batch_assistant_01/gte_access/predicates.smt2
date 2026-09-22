; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun caller () ReportAddress)
(declare-fun designated_distributor () ReportAddress)
(declare-fun rewards_deactivated () Bool)
(assert
 (= caller caller))
(assert
 (= designated_distributor designated_distributor))
(assert
 (= rewards_deactivated rewards_deactivated))
(define-fun report_preconditions () Bool (distinct caller designated_distributor))
(define-fun report_safety () Bool (=> (distinct caller designated_distributor) (not rewards_deactivated)))
