; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c937d61e9_accounting_quote_asset () ReportAddress)
(declare-fun c937d61e9_canonical_quote_asset () ReportAddress)
(declare-fun c937d61e9_fake_token_approved () Bool)
(declare-fun c937d61e9_pool_total_shares () Int)
(declare-fun c937d61e9_quote_claims_dos () Bool)
(assert
 (= c937d61e9_accounting_quote_asset c937d61e9_accounting_quote_asset))
(assert
 (= c937d61e9_canonical_quote_asset c937d61e9_canonical_quote_asset))
(assert
 (= c937d61e9_fake_token_approved c937d61e9_fake_token_approved))
(assert
 (= c937d61e9_pool_total_shares c937d61e9_pool_total_shares))
(assert
 (= c937d61e9_quote_claims_dos c937d61e9_quote_claims_dos))
(define-fun report_preconditions () Bool (and (< 0 c937d61e9_pool_total_shares) c937d61e9_fake_token_approved))
(define-fun report_safety () Bool (=> c937d61e9_fake_token_approved
    (= c937d61e9_accounting_quote_asset c937d61e9_canonical_quote_asset)))
(define-fun report_effects () Bool (and c937d61e9_fake_token_approved
     (not (= c937d61e9_accounting_quote_asset c937d61e9_canonical_quote_asset))
     c937d61e9_quote_claims_dos
     c937d61e9_quote_claims_dos))
(assert report_preconditions)
(check-sat)
(get-model)
