; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4a095ade_quote_reserve () Int)
(declare-fun c4a095ade_quote_reserve_low () Bool)
(declare-fun c4a095ade_sell_completed () Bool)
(declare-fun c4a095ade_virtual_quote () Int)
(assert
 (= c4a095ade_quote_reserve c4a095ade_quote_reserve))
(assert
 (= c4a095ade_quote_reserve_low c4a095ade_quote_reserve_low))
(assert
 (= c4a095ade_sell_completed c4a095ade_sell_completed))
(assert
 (= c4a095ade_virtual_quote c4a095ade_virtual_quote))
(define-fun report_preconditions () Bool (and c4a095ade_quote_reserve_low
     (< c4a095ade_quote_reserve c4a095ade_virtual_quote)))
(define-fun report_safety () Bool (=> (and c4a095ade_quote_reserve_low
         (< c4a095ade_quote_reserve c4a095ade_virtual_quote))
    c4a095ade_sell_completed))
(define-fun report_effects () Bool (and c4a095ade_quote_reserve_low
     (< c4a095ade_quote_reserve c4a095ade_virtual_quote)
     (not c4a095ade_sell_completed)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
