; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1c3158e9_init_market_completed () Bool)
(declare-fun c1c3158e9_lookup_keyed_by_quote_token () Bool)
(declare-fun c1c3158e9_market_params_have_tokens () Bool)
(declare-fun c1c3158e9_quote_token_keyed_default_exists () Bool)
(assert
 (= c1c3158e9_init_market_completed c1c3158e9_init_market_completed))
(assert
 (= c1c3158e9_lookup_keyed_by_quote_token c1c3158e9_lookup_keyed_by_quote_token))
(assert
 (= c1c3158e9_market_params_have_tokens c1c3158e9_market_params_have_tokens))
(assert
 (= c1c3158e9_quote_token_keyed_default_exists c1c3158e9_quote_token_keyed_default_exists))
(define-fun report_preconditions () Bool (and c1c3158e9_quote_token_keyed_default_exists
     c1c3158e9_market_params_have_tokens))
(define-fun report_safety () Bool (=> (and c1c3158e9_quote_token_keyed_default_exists
         c1c3158e9_market_params_have_tokens)
    (and c1c3158e9_lookup_keyed_by_quote_token c1c3158e9_init_market_completed)))
(define-fun report_effects () Bool (and c1c3158e9_quote_token_keyed_default_exists
     c1c3158e9_market_params_have_tokens
     (not (and c1c3158e9_lookup_keyed_by_quote_token
               c1c3158e9_init_market_completed))))
