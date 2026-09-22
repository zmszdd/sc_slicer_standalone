; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun lot_size_in_base () Int)
(declare-fun fok_buy_amount () Int)
(declare-fun order_amount_after_match () Int)
(declare-fun tradeable_filled () Bool)
(declare-fun dust_remainder () Bool)
(declare-fun revert_occurred () Bool)
(assert
 (= lot_size_in_base lot_size_in_base))
(assert
 (= fok_buy_amount fok_buy_amount))
(assert
 (= order_amount_after_match order_amount_after_match))
(assert
 (= tradeable_filled tradeable_filled))
(assert
 (= dust_remainder dust_remainder))
(assert
 (= revert_occurred revert_occurred))
(define-fun report_preconditions () Bool (and (= 1000000000000000001 lot_size_in_base)
     (= 100500000000000000001 fok_buy_amount)
     dust_remainder))
(define-fun report_safety () Bool (=> (and tradeable_filled dust_remainder) (not revert_occurred)))
(define-fun report_effects () Bool (and tradeable_filled dust_remainder (not (not revert_occurred))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
