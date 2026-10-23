; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cad23afbc_applied_cap_limit_from_base_key () Bool)
(declare-fun cad23afbc_applied_cap_limit_from_quote_key () Bool)
(declare-fun cad23afbc_default_override_keyed_by_quote () Bool)
(declare-fun cad23afbc_market_params_has_base_and_quote () Bool)
(assert
 (= cad23afbc_applied_cap_limit_from_base_key cad23afbc_applied_cap_limit_from_base_key))
(assert
 (= cad23afbc_applied_cap_limit_from_quote_key cad23afbc_applied_cap_limit_from_quote_key))
(assert
 (= cad23afbc_default_override_keyed_by_quote cad23afbc_default_override_keyed_by_quote))
(assert
 (= cad23afbc_market_params_has_base_and_quote cad23afbc_market_params_has_base_and_quote))
(define-fun report_preconditions () Bool (and cad23afbc_default_override_keyed_by_quote
     cad23afbc_market_params_has_base_and_quote))
(define-fun report_safety () Bool (=> (and cad23afbc_default_override_keyed_by_quote
         cad23afbc_market_params_has_base_and_quote)
    (and cad23afbc_applied_cap_limit_from_quote_key
         (not cad23afbc_applied_cap_limit_from_base_key))))
(define-fun report_effects () Bool (and cad23afbc_default_override_keyed_by_quote
     cad23afbc_market_params_has_base_and_quote
     (not (and cad23afbc_applied_cap_limit_from_quote_key
               (not cad23afbc_applied_cap_limit_from_base_key)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
