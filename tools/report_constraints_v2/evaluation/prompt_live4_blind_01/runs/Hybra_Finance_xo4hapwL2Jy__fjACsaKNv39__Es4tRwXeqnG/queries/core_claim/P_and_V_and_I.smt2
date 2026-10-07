; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun zero_address () ReportAddress)
(declare-fun rhybr_address () ReportAddress)
(declare-fun setrhybr_enforced () Bool)
(declare-fun rewards_present () Bool)
(declare-fun withdrawal_completed () Bool)
(assert
 (= zero_address zero_address))
(assert
 (= rhybr_address rhybr_address))
(assert
 (= setrhybr_enforced setrhybr_enforced))
(assert
 (= rewards_present rewards_present))
(assert
 (= withdrawal_completed withdrawal_completed))
(define-fun report_preconditions () Bool (and (= rhybr_address zero_address)
     (not setrhybr_enforced)
     (= rhybr_address zero_address)
     rewards_present))
(define-fun report_safety () Bool (=> (and (= rhybr_address zero_address) rewards_present) withdrawal_completed))
(define-fun report_effects () Bool (and (= rhybr_address zero_address) rewards_present (not withdrawal_completed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
