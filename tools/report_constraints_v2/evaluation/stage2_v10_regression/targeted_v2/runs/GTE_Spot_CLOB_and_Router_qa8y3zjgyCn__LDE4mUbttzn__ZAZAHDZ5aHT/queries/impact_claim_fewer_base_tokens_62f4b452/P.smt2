; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c59d12591_amount_is_base () Bool)
(declare-fun c59d12591_base_delta () Int)
(declare-fun c59d12591_lot_size_in_base () Int)
(declare-fun c59d12591_maker_base_available () Int)
(declare-fun c59d12591_matched_base () Int)
(declare-fun c59d12591_remaining_quote_amount () Int)
(assert
 (= c59d12591_amount_is_base c59d12591_amount_is_base))
(assert
 (= c59d12591_base_delta c59d12591_base_delta))
(assert
 (= c59d12591_lot_size_in_base c59d12591_lot_size_in_base))
(assert
 (= c59d12591_maker_base_available c59d12591_maker_base_available))
(assert
 (= c59d12591_matched_base c59d12591_matched_base))
(assert
 (= c59d12591_remaining_quote_amount c59d12591_remaining_quote_amount))
(define-fun report_preconditions () Bool (and (not c59d12591_amount_is_base)
     (= 1000000000000000000 c59d12591_lot_size_in_base)
     (= 2500000000000000000 c59d12591_remaining_quote_amount)
     (= 3000000000000000000 c59d12591_maker_base_available)
     (= 2000000000000000000 c59d12591_base_delta)
     (= 2500000000000000000 c59d12591_matched_base)
     (distinct c59d12591_base_delta c59d12591_matched_base)))
(define-fun report_safety () Bool (=> (and (not c59d12591_amount_is_base)
         (= 1000000000000000000 c59d12591_lot_size_in_base)
         (= 2500000000000000000 c59d12591_remaining_quote_amount)
         (= 3000000000000000000 c59d12591_maker_base_available))
    (>= c59d12591_base_delta c59d12591_matched_base)))
(define-fun report_effects () Bool (and (not c59d12591_amount_is_base)
     (= 1000000000000000000 c59d12591_lot_size_in_base)
     (= 2500000000000000000 c59d12591_remaining_quote_amount)
     (= 3000000000000000000 c59d12591_maker_base_available)
     (not (>= c59d12591_base_delta c59d12591_matched_base))))
(assert report_preconditions)
(check-sat)
(get-model)
