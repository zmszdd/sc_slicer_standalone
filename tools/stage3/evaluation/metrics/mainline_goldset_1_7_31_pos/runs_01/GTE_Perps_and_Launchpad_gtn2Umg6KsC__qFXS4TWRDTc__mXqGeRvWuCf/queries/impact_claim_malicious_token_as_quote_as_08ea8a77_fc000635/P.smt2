; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c324bda19_malicious_token_used_as_quote_asset () Bool)
(declare-fun c324bda19_quote_asset_param () ReportAddress)
(declare-fun c324bda19_stored_quote_asset () ReportAddress)
(assert
 (= c324bda19_malicious_token_used_as_quote_asset c324bda19_malicious_token_used_as_quote_asset))
(assert
 (= c324bda19_quote_asset_param c324bda19_quote_asset_param))
(assert
 (= c324bda19_stored_quote_asset c324bda19_stored_quote_asset))
(define-fun report_preconditions () Bool (and c324bda19_malicious_token_used_as_quote_asset
     c324bda19_malicious_token_used_as_quote_asset))
(define-fun report_safety () Bool (= c324bda19_quote_asset_param c324bda19_stored_quote_asset))
(define-fun report_effects () Bool (and c324bda19_malicious_token_used_as_quote_asset
     (not (= c324bda19_quote_asset_param c324bda19_stored_quote_asset))
     c324bda19_malicious_token_used_as_quote_asset
     c324bda19_malicious_token_used_as_quote_asset))
(assert report_preconditions)
(check-sat)
(get-model)
