; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8c66f32d_borrow_value () Int)
(declare-fun c8c66f32d_real_net_assets () Int)
(declare-fun c8c66f32d_reported_backing () Int)
(declare-fun c8c66f32d_surplus_computed () Int)
(assert
 (= c8c66f32d_borrow_value c8c66f32d_borrow_value))
(assert
 (= c8c66f32d_real_net_assets c8c66f32d_real_net_assets))
(assert
 (= c8c66f32d_reported_backing c8c66f32d_reported_backing))
(assert
 (= c8c66f32d_surplus_computed c8c66f32d_surplus_computed))
(define-fun report_preconditions () Bool (and (< 0 c8c66f32d_borrow_value) (<= 0 c8c66f32d_surplus_computed)))
(define-fun report_safety () Bool (=> (= c8c66f32d_real_net_assets
       (- c8c66f32d_reported_backing c8c66f32d_borrow_value))
    (=> (and (< 0 c8c66f32d_borrow_value) (<= 0 c8c66f32d_surplus_computed))
        (<= c8c66f32d_reported_backing c8c66f32d_real_net_assets))))
(define-fun report_effects () Bool (and (= c8c66f32d_real_net_assets
        (- c8c66f32d_reported_backing c8c66f32d_borrow_value))
     (< 0 c8c66f32d_borrow_value)
     (<= 0 c8c66f32d_surplus_computed)
     (not (<= c8c66f32d_reported_backing c8c66f32d_real_net_assets))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
