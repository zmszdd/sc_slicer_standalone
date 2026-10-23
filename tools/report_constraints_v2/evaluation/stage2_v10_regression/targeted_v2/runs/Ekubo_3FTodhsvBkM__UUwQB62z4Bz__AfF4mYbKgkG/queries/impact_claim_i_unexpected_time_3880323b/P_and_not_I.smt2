; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7df70581_deadline_specified () Bool)
(declare-fun c7df70581_executed_at_unexpected_time () Bool)
(declare-fun c7df70581_slippage_only_protection () Bool)
(assert
 (= c7df70581_deadline_specified c7df70581_deadline_specified))
(assert
 (= c7df70581_executed_at_unexpected_time c7df70581_executed_at_unexpected_time))
(assert
 (= c7df70581_slippage_only_protection c7df70581_slippage_only_protection))
(define-fun report_preconditions () Bool (and (not c7df70581_deadline_specified) c7df70581_slippage_only_protection))
(define-fun report_safety () Bool (=> (and (not c7df70581_deadline_specified) c7df70581_slippage_only_protection)
    (not c7df70581_executed_at_unexpected_time)))
(define-fun report_effects () Bool (and (not c7df70581_deadline_specified)
     c7df70581_slippage_only_protection
     (not (not c7df70581_executed_at_unexpected_time))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
