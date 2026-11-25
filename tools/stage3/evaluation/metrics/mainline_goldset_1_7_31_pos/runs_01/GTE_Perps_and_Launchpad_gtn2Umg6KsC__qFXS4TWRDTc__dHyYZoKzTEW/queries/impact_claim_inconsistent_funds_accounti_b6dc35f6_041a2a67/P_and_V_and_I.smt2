; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c637cead9_accounting_token_key () ReportAddress)
(declare-fun c637cead9_canonical_quote_asset () ReportAddress)
(declare-fun c637cead9_fake_token_approved () Bool)
(declare-fun c637cead9_pool_total_shares () Int)
(declare-fun c637cead9_user_pending_quote_positive () Bool)
(assert
 (= c637cead9_accounting_token_key c637cead9_accounting_token_key))
(assert
 (= c637cead9_canonical_quote_asset c637cead9_canonical_quote_asset))
(assert
 (= c637cead9_fake_token_approved c637cead9_fake_token_approved))
(assert
 (= c637cead9_pool_total_shares c637cead9_pool_total_shares))
(assert
 (= c637cead9_user_pending_quote_positive c637cead9_user_pending_quote_positive))
(define-fun report_preconditions () Bool (and (< 0 c637cead9_pool_total_shares)
     c637cead9_fake_token_approved
     c637cead9_user_pending_quote_positive))
(define-fun report_safety () Bool (= c637cead9_accounting_token_key c637cead9_canonical_quote_asset))
(define-fun report_effects () Bool (and c637cead9_user_pending_quote_positive
     (not (= c637cead9_accounting_token_key c637cead9_canonical_quote_asset))
     c637cead9_user_pending_quote_positive
     (distinct c637cead9_accounting_token_key c637cead9_canonical_quote_asset)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
