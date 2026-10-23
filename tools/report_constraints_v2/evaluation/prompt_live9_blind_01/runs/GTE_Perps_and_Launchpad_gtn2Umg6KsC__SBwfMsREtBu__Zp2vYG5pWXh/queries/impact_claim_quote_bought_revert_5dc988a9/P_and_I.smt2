; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6beab471_quote_bought_reverts () Bool)
(declare-fun c6beab471_quote_reserve () Int)
(declare-fun c6beab471_virtual_quote () Int)
(assert
 (= c6beab471_quote_bought_reverts c6beab471_quote_bought_reverts))
(assert
 (= c6beab471_quote_reserve c6beab471_quote_reserve))
(assert
 (= c6beab471_virtual_quote c6beab471_virtual_quote))
(define-fun report_preconditions () Bool (< c6beab471_quote_reserve c6beab471_virtual_quote))
(define-fun report_safety () Bool (=> (< c6beab471_quote_reserve c6beab471_virtual_quote)
    (not c6beab471_quote_bought_reverts)))
(define-fun report_effects () Bool (and (< c6beab471_quote_reserve c6beab471_virtual_quote)
     (not (not c6beab471_quote_bought_reverts))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
