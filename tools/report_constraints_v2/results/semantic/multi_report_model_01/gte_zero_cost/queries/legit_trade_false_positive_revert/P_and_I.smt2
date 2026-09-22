; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun amount_and_zero () Bool)
(declare-fun amount_a_nonzero () Bool)
(declare-fun amount_b_nonzero () Bool)
(declare-fun zero_cost_trade () Bool)
(declare-fun trade_blocked () Bool)
(assert
 (= amount_and_zero amount_and_zero))
(assert
 (= amount_a_nonzero amount_a_nonzero))
(assert
 (= amount_b_nonzero amount_b_nonzero))
(assert
 (= zero_cost_trade zero_cost_trade))
(assert
 (= trade_blocked trade_blocked))
(define-fun report_preconditions () Bool (and amount_and_zero amount_a_nonzero amount_b_nonzero))
(define-fun report_safety () Bool (=> zero_cost_trade trade_blocked))
(define-fun report_effects () Bool trade_blocked)
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
