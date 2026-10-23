; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c61a46d92_amount_is_base () Bool)
(declare-fun c61a46d92_base_delta () Int)
(declare-fun c61a46d92_fok_validation_passes () Bool)
(declare-fun c61a46d92_lot_size_in_base () Int)
(declare-fun c61a46d92_maker_base_available () Int)
(declare-fun c61a46d92_matched_base () Int)
(declare-fun c61a46d92_quote_remains_unfilled () Bool)
(declare-fun c61a46d92_remaining_quote () Int)
(assert
 (= c61a46d92_amount_is_base c61a46d92_amount_is_base))
(assert
 (= c61a46d92_base_delta c61a46d92_base_delta))
(assert
 (= c61a46d92_fok_validation_passes c61a46d92_fok_validation_passes))
(assert
 (= c61a46d92_lot_size_in_base c61a46d92_lot_size_in_base))
(assert
 (= c61a46d92_maker_base_available c61a46d92_maker_base_available))
(assert
 (= c61a46d92_matched_base c61a46d92_matched_base))
(assert
 (= c61a46d92_quote_remains_unfilled c61a46d92_quote_remains_unfilled))
(assert
 (= c61a46d92_remaining_quote c61a46d92_remaining_quote))
(define-fun report_preconditions () Bool (and (not c61a46d92_amount_is_base)
     (= 1000000000000000000 c61a46d92_lot_size_in_base)
     (= 2500000000000000000 c61a46d92_remaining_quote)
     (= 3000000000000000000 c61a46d92_maker_base_available)
     (distinct c61a46d92_base_delta c61a46d92_matched_base)))
(define-fun report_safety () Bool (=> (and (not c61a46d92_amount_is_base)
         (distinct c61a46d92_base_delta c61a46d92_matched_base))
    (or (not c61a46d92_fok_validation_passes)
        (not c61a46d92_quote_remains_unfilled))))
(define-fun report_effects () Bool (and (not c61a46d92_amount_is_base)
     (distinct c61a46d92_base_delta c61a46d92_matched_base)
     (not (or (not c61a46d92_fok_validation_passes)
              (not c61a46d92_quote_remains_unfilled)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
