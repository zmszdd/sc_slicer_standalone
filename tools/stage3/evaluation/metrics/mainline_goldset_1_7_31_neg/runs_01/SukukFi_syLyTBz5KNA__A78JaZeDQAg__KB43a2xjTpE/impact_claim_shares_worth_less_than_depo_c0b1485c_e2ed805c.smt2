; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c93e8d3c1_deposit_request_initiated_occurred () Bool)
(declare-fun c93e8d3c1_fulfill_uses_reversible_value () Bool)
(declare-fun c93e8d3c1_shares_worth_less_than_deposit_observed () Bool)
(declare-fun c93e8d3c1_yield_recorded_before_fulfill_occurred () Bool)
(assert
 (= c93e8d3c1_deposit_request_initiated_occurred c93e8d3c1_deposit_request_initiated_occurred))
(assert
 (= c93e8d3c1_fulfill_uses_reversible_value c93e8d3c1_fulfill_uses_reversible_value))
(assert
 (= c93e8d3c1_shares_worth_less_than_deposit_observed c93e8d3c1_shares_worth_less_than_deposit_observed))
(assert
 (= c93e8d3c1_yield_recorded_before_fulfill_occurred c93e8d3c1_yield_recorded_before_fulfill_occurred))
(define-fun report_preconditions () Bool (and c93e8d3c1_deposit_request_initiated_occurred
     c93e8d3c1_yield_recorded_before_fulfill_occurred))
(define-fun report_safety () Bool (=> c93e8d3c1_deposit_request_initiated_occurred
    (= c93e8d3c1_fulfill_uses_reversible_value false)))
(define-fun report_effects () Bool (and c93e8d3c1_deposit_request_initiated_occurred
     (not (= c93e8d3c1_fulfill_uses_reversible_value false))
     c93e8d3c1_shares_worth_less_than_deposit_observed
     c93e8d3c1_shares_worth_less_than_deposit_observed))
