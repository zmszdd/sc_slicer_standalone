; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c046c96c5_borrow_value () Int)
(declare-fun c046c96c5_keeper_computes_surplus () Bool)
(declare-fun c046c96c5_settle_accepts_unbacked () Bool)
(assert
 (= c046c96c5_borrow_value c046c96c5_borrow_value))
(assert
 (= c046c96c5_keeper_computes_surplus c046c96c5_keeper_computes_surplus))
(assert
 (= c046c96c5_settle_accepts_unbacked c046c96c5_settle_accepts_unbacked))
(define-fun report_preconditions () Bool (and (< 0 c046c96c5_borrow_value) c046c96c5_keeper_computes_surplus))
(define-fun report_safety () Bool (=> (and (< 0 c046c96c5_borrow_value) c046c96c5_keeper_computes_surplus)
    (not c046c96c5_settle_accepts_unbacked)))
(define-fun report_effects () Bool (and (< 0 c046c96c5_borrow_value)
     c046c96c5_keeper_computes_surplus
     (not (not c046c96c5_settle_accepts_unbacked))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
