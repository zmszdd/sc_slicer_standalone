; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6f89d7f5_applied_no_cap_limit () Int)
(declare-fun c6f89d7f5_default_override_keyed_by_quote_token () Bool)
(declare-fun c6f89d7f5_intended_quote_token_no_cap_limit () Int)
(declare-fun c6f89d7f5_market_params_has_base_and_quote () Bool)
(declare-fun c6f89d7f5_unexpected_mint_redeem_behavior_occurred () Bool)
(assert
 (= c6f89d7f5_applied_no_cap_limit c6f89d7f5_applied_no_cap_limit))
(assert
 (= c6f89d7f5_default_override_keyed_by_quote_token c6f89d7f5_default_override_keyed_by_quote_token))
(assert
 (= c6f89d7f5_intended_quote_token_no_cap_limit c6f89d7f5_intended_quote_token_no_cap_limit))
(assert
 (= c6f89d7f5_market_params_has_base_and_quote c6f89d7f5_market_params_has_base_and_quote))
(assert
 (= c6f89d7f5_unexpected_mint_redeem_behavior_occurred c6f89d7f5_unexpected_mint_redeem_behavior_occurred))
(define-fun report_preconditions () Bool (and c6f89d7f5_default_override_keyed_by_quote_token
     c6f89d7f5_market_params_has_base_and_quote))
(define-fun report_safety () Bool (=> (and c6f89d7f5_default_override_keyed_by_quote_token
         c6f89d7f5_market_params_has_base_and_quote)
    (or (= c6f89d7f5_applied_no_cap_limit
           c6f89d7f5_intended_quote_token_no_cap_limit)
        (not c6f89d7f5_unexpected_mint_redeem_behavior_occurred))))
(define-fun report_effects () Bool (and c6f89d7f5_default_override_keyed_by_quote_token
     c6f89d7f5_market_params_has_base_and_quote
     (not (or (= c6f89d7f5_applied_no_cap_limit
                 c6f89d7f5_intended_quote_token_no_cap_limit)
              (not c6f89d7f5_unexpected_mint_redeem_behavior_occurred)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
