; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c121c37bb_dynamic_fee_value () Int)
(declare-fun c121c37bb_factory_fee_reject_threshold () Int)
(declare-fun c121c37bb_fee_accepted_by_factory () Bool)
(declare-fun c121c37bb_max_fee_cap () Int)
(assert
 (= c121c37bb_dynamic_fee_value c121c37bb_dynamic_fee_value))
(assert
 (= c121c37bb_factory_fee_reject_threshold c121c37bb_factory_fee_reject_threshold))
(assert
 (= c121c37bb_fee_accepted_by_factory c121c37bb_fee_accepted_by_factory))
(assert
 (= c121c37bb_max_fee_cap c121c37bb_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 c121c37bb_max_fee_cap)
     (= 100000 c121c37bb_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> (and (< 100000 c121c37bb_dynamic_fee_value)
         (>= 500000 c121c37bb_dynamic_fee_value))
    (=> (and (< 0 c121c37bb_dynamic_fee_value)
             (>= 500000 c121c37bb_dynamic_fee_value))
        c121c37bb_fee_accepted_by_factory)))
(define-fun report_effects () Bool (and (< 100000 c121c37bb_dynamic_fee_value)
     (>= 500000 c121c37bb_dynamic_fee_value)
     (< 0 c121c37bb_dynamic_fee_value)
     (>= 500000 c121c37bb_dynamic_fee_value)
     (not c121c37bb_fee_accepted_by_factory)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
