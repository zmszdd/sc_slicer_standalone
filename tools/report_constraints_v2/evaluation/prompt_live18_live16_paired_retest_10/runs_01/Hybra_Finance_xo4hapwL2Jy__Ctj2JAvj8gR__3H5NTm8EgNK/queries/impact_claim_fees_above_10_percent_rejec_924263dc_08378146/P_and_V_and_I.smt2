; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c60c9174a_dynamic_fee_value () Int)
(declare-fun c60c9174a_fee_accepted_by_factory () Bool)
(declare-fun c60c9174a_max_fee_cap () Int)
(assert
 (= c60c9174a_dynamic_fee_value c60c9174a_dynamic_fee_value))
(assert
 (= c60c9174a_fee_accepted_by_factory c60c9174a_fee_accepted_by_factory))
(assert
 (= c60c9174a_max_fee_cap c60c9174a_max_fee_cap))
(define-fun report_preconditions () Bool (< 100000 c60c9174a_dynamic_fee_value))
(define-fun report_safety () Bool (=> (and (< 100000 c60c9174a_dynamic_fee_value)
         (<= c60c9174a_dynamic_fee_value c60c9174a_max_fee_cap))
    (=> (and (< 100000 c60c9174a_dynamic_fee_value)
             (<= c60c9174a_dynamic_fee_value c60c9174a_max_fee_cap))
        c60c9174a_fee_accepted_by_factory)))
(define-fun report_effects () Bool (and (and (< 100000 c60c9174a_dynamic_fee_value)
          (<= c60c9174a_dynamic_fee_value c60c9174a_max_fee_cap))
     (and (< 100000 c60c9174a_dynamic_fee_value)
          (<= c60c9174a_dynamic_fee_value c60c9174a_max_fee_cap))
     (not c60c9174a_fee_accepted_by_factory)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
