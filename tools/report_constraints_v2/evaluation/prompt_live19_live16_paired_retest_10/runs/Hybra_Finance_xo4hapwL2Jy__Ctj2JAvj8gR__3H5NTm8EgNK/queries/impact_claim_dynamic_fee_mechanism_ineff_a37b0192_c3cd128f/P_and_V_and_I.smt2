; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf14fa0d1_computed_dynamic_fee () Int)
(declare-fun cf14fa0d1_factory_fee_threshold () Int)
(declare-fun cf14fa0d1_module_max_fee_cap () Int)
(assert
 (= cf14fa0d1_computed_dynamic_fee cf14fa0d1_computed_dynamic_fee))
(assert
 (= cf14fa0d1_factory_fee_threshold cf14fa0d1_factory_fee_threshold))
(assert
 (= cf14fa0d1_module_max_fee_cap cf14fa0d1_module_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 cf14fa0d1_module_max_fee_cap)
     (= 100000 cf14fa0d1_factory_fee_threshold)))
(define-fun report_safety () Bool (=> (> cf14fa0d1_computed_dynamic_fee cf14fa0d1_factory_fee_threshold)
    (=> (<= cf14fa0d1_computed_dynamic_fee cf14fa0d1_module_max_fee_cap)
        (<= cf14fa0d1_computed_dynamic_fee cf14fa0d1_module_max_fee_cap))))
(define-fun report_effects () Bool (and (> cf14fa0d1_computed_dynamic_fee cf14fa0d1_factory_fee_threshold)
     (<= cf14fa0d1_computed_dynamic_fee cf14fa0d1_module_max_fee_cap)
     (not (<= cf14fa0d1_computed_dynamic_fee cf14fa0d1_module_max_fee_cap))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
