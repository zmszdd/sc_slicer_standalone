; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun time_weighted_average () Int)
(declare-fun trade_price () Int)
(declare-fun olas_received () Int)
(declare-fun amount_out_min () Int)
(assert
 (= time_weighted_average time_weighted_average))
(assert
 (= trade_price trade_price))
(assert
 (= olas_received olas_received))
(assert
 (= amount_out_min amount_out_min))
(define-fun report_preconditions () Bool (= time_weighted_average trade_price))
(define-fun report_safety () Bool (=> (= time_weighted_average trade_price) (>= olas_received amount_out_min)))
(define-fun report_effects () Bool (and (= time_weighted_average trade_price)
     (not (>= olas_received amount_out_min))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
