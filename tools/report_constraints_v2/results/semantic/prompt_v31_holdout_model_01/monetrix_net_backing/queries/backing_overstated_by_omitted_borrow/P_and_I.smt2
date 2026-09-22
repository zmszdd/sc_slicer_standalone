; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun supply_value () Int)
(declare-fun borrow_value () Int)
(declare-fun total_backing_signed () Int)
(assert
 (= supply_value supply_value))
(assert
 (= borrow_value borrow_value))
(assert
 (= total_backing_signed total_backing_signed))
(define-fun report_preconditions () Bool (< 0 borrow_value))
(define-fun report_safety () Bool (=> (< 0 borrow_value) (<= total_backing_signed (- supply_value borrow_value))))
(define-fun report_effects () Bool (and (< 0 borrow_value) (> total_backing_signed (- supply_value borrow_value))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
