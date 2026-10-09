; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun amount_in_base () Int)
(declare-fun quote_amount () Int)
(declare-fun guard_uses_bitwise_and () Bool)
(declare-fun guard_zero_condition_true () Bool)
(declare-fun trade_reverted () Bool)
(assert
 (= amount_in_base amount_in_base))
(assert
 (= quote_amount quote_amount))
(assert
 (= guard_uses_bitwise_and guard_uses_bitwise_and))
(assert
 (= guard_zero_condition_true guard_zero_condition_true))
(assert
 (= trade_reverted trade_reverted))
(define-fun report_preconditions () Bool (and (= 1 amount_in_base) (= 2 quote_amount) guard_uses_bitwise_and))
(define-fun report_safety () Bool (=> (and (= 1 amount_in_base) (= 2 quote_amount) guard_zero_condition_true)
    trade_reverted))
(define-fun report_effects () Bool (and (= 1 amount_in_base)
     (= 2 quote_amount)
     guard_zero_condition_true
     (not trade_reverted)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
