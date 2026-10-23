; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c71fa0f1c_dynamic_fee_value () Int)
(declare-fun c71fa0f1c_fee_rejected () Bool)
(declare-fun c71fa0f1c_get_swap_fee_threshold () Int)
(declare-fun c71fa0f1c_max_fee_cap () Int)
(assert
 (= c71fa0f1c_dynamic_fee_value c71fa0f1c_dynamic_fee_value))
(assert
 (= c71fa0f1c_fee_rejected c71fa0f1c_fee_rejected))
(assert
 (= c71fa0f1c_get_swap_fee_threshold c71fa0f1c_get_swap_fee_threshold))
(assert
 (= c71fa0f1c_max_fee_cap c71fa0f1c_max_fee_cap))
(define-fun report_preconditions () Bool (and (< 100000 c71fa0f1c_dynamic_fee_value)
     (= 100000 c71fa0f1c_get_swap_fee_threshold)))
(define-fun report_safety () Bool (=> (and (< 100000 c71fa0f1c_dynamic_fee_value) c71fa0f1c_fee_rejected)
    (=> (<= c71fa0f1c_dynamic_fee_value c71fa0f1c_max_fee_cap)
        (<= c71fa0f1c_dynamic_fee_value c71fa0f1c_max_fee_cap))))
(define-fun report_effects () Bool (and (< 100000 c71fa0f1c_dynamic_fee_value)
     c71fa0f1c_fee_rejected
     (<= c71fa0f1c_dynamic_fee_value c71fa0f1c_max_fee_cap)
     (not (<= c71fa0f1c_dynamic_fee_value c71fa0f1c_max_fee_cap))))
