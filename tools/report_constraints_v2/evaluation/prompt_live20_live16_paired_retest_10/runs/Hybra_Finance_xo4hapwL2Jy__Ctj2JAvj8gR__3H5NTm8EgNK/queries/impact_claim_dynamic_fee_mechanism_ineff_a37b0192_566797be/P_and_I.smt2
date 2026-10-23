; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3cc3754d_dynamic_fee_applied () Bool)
(declare-fun c3cc3754d_dynamic_fee_mechanism_ineffective_observed () Bool)
(declare-fun c3cc3754d_max_fee_cap () Int)
(assert
 (= c3cc3754d_dynamic_fee_applied c3cc3754d_dynamic_fee_applied))
(assert
 (= c3cc3754d_dynamic_fee_mechanism_ineffective_observed c3cc3754d_dynamic_fee_mechanism_ineffective_observed))
(assert
 (= c3cc3754d_max_fee_cap c3cc3754d_max_fee_cap))
(define-fun report_preconditions () Bool (= 500000 c3cc3754d_max_fee_cap))
(define-fun report_safety () Bool (=> c3cc3754d_dynamic_fee_applied c3cc3754d_dynamic_fee_applied))
(define-fun report_effects () Bool (and c3cc3754d_dynamic_fee_mechanism_ineffective_observed
     c3cc3754d_dynamic_fee_mechanism_ineffective_observed))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
