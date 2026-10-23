; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf638d35e_computed_dynamic_fee () Int)
(declare-fun cf638d35e_dynamic_fee_accepted_and_applied () Bool)
(declare-fun cf638d35e_factory_fee_reject_threshold () Int)
(declare-fun cf638d35e_module_max_fee_cap () Int)
(assert
 (= cf638d35e_computed_dynamic_fee cf638d35e_computed_dynamic_fee))
(assert
 (= cf638d35e_dynamic_fee_accepted_and_applied cf638d35e_dynamic_fee_accepted_and_applied))
(assert
 (= cf638d35e_factory_fee_reject_threshold cf638d35e_factory_fee_reject_threshold))
(assert
 (= cf638d35e_module_max_fee_cap cf638d35e_module_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 cf638d35e_module_max_fee_cap)
     (= 100000 cf638d35e_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> (> cf638d35e_computed_dynamic_fee cf638d35e_factory_fee_reject_threshold)
    (=> (and (<= cf638d35e_computed_dynamic_fee cf638d35e_module_max_fee_cap)
             (< 0 cf638d35e_computed_dynamic_fee))
        cf638d35e_dynamic_fee_accepted_and_applied)))
(define-fun report_effects () Bool (and (> cf638d35e_computed_dynamic_fee cf638d35e_factory_fee_reject_threshold)
     (<= cf638d35e_computed_dynamic_fee cf638d35e_module_max_fee_cap)
     (< 0 cf638d35e_computed_dynamic_fee)
     (not cf638d35e_dynamic_fee_accepted_and_applied)))
(assert report_preconditions)
(check-sat)
(get-model)
