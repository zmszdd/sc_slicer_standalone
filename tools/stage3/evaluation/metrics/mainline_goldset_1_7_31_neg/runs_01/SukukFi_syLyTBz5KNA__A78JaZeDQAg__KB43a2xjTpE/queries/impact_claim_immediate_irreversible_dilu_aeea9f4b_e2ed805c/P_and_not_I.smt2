; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8f334ca0_deposit_diluted () Bool)
(declare-fun c8f334ca0_deposit_request_initiated_occurred () Bool)
(declare-fun c8f334ca0_fulfill_uses_irreversible_value () Bool)
(declare-fun c8f334ca0_fulfill_uses_reversible_value () Bool)
(declare-fun c8f334ca0_yield_recorded_before_fulfill_occurred () Bool)
(assert
 (= c8f334ca0_deposit_diluted c8f334ca0_deposit_diluted))
(assert
 (= c8f334ca0_deposit_request_initiated_occurred c8f334ca0_deposit_request_initiated_occurred))
(assert
 (= c8f334ca0_fulfill_uses_irreversible_value c8f334ca0_fulfill_uses_irreversible_value))
(assert
 (= c8f334ca0_fulfill_uses_reversible_value c8f334ca0_fulfill_uses_reversible_value))
(assert
 (= c8f334ca0_yield_recorded_before_fulfill_occurred c8f334ca0_yield_recorded_before_fulfill_occurred))
(define-fun report_preconditions () Bool (and c8f334ca0_deposit_request_initiated_occurred
     c8f334ca0_yield_recorded_before_fulfill_occurred))
(define-fun report_safety () Bool (=> c8f334ca0_deposit_request_initiated_occurred
    (= c8f334ca0_fulfill_uses_reversible_value
       c8f334ca0_fulfill_uses_irreversible_value)))
(define-fun report_effects () Bool (and c8f334ca0_deposit_request_initiated_occurred
     (not (= c8f334ca0_fulfill_uses_reversible_value
             c8f334ca0_fulfill_uses_irreversible_value))
     c8f334ca0_deposit_diluted))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
