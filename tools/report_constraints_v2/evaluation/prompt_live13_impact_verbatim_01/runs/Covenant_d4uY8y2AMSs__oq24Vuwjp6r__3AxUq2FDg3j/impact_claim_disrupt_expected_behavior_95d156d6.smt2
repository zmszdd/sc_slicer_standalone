; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4825241b_default_override_keyed_by_quote_token () Bool)
(declare-fun c4825241b_expected_behavior_disrupted () Bool)
(declare-fun c4825241b_lookup_keyed_by_quote_token () Bool)
(declare-fun c4825241b_market_params_has_base_and_quote () Bool)
(assert
 (= c4825241b_default_override_keyed_by_quote_token c4825241b_default_override_keyed_by_quote_token))
(assert
 (= c4825241b_expected_behavior_disrupted c4825241b_expected_behavior_disrupted))
(assert
 (= c4825241b_lookup_keyed_by_quote_token c4825241b_lookup_keyed_by_quote_token))
(assert
 (= c4825241b_market_params_has_base_and_quote c4825241b_market_params_has_base_and_quote))
(define-fun report_preconditions () Bool (and c4825241b_default_override_keyed_by_quote_token
     c4825241b_market_params_has_base_and_quote))
(define-fun report_safety () Bool (=> (and c4825241b_default_override_keyed_by_quote_token
         c4825241b_market_params_has_base_and_quote)
    (or c4825241b_lookup_keyed_by_quote_token
        (not c4825241b_expected_behavior_disrupted))))
(define-fun report_effects () Bool (and c4825241b_default_override_keyed_by_quote_token
     c4825241b_market_params_has_base_and_quote
     (not (or c4825241b_lookup_keyed_by_quote_token
              (not c4825241b_expected_behavior_disrupted)))))
