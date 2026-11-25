; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbac4c4d8_base_is_power_of_two () Bool)
(declare-fun cbac4c4d8_impact_base_amount () Int)
(declare-fun cbac4c4d8_impact_quote_amount () Int)
(declare-fun cbac4c4d8_impact_revert_occurred () Bool)
(declare-fun cbac4c4d8_legitimate_match_rejected () Bool)
(declare-fun cbac4c4d8_matched_base_amount () Int)
(declare-fun cbac4c4d8_matched_quote_amount () Int)
(assert
 (= cbac4c4d8_base_is_power_of_two cbac4c4d8_base_is_power_of_two))
(assert
 (= cbac4c4d8_impact_base_amount cbac4c4d8_impact_base_amount))
(assert
 (= cbac4c4d8_impact_quote_amount cbac4c4d8_impact_quote_amount))
(assert
 (= cbac4c4d8_impact_revert_occurred cbac4c4d8_impact_revert_occurred))
(assert
 (= cbac4c4d8_legitimate_match_rejected cbac4c4d8_legitimate_match_rejected))
(assert
 (= cbac4c4d8_matched_base_amount cbac4c4d8_matched_base_amount))
(assert
 (= cbac4c4d8_matched_quote_amount cbac4c4d8_matched_quote_amount))
(define-fun report_preconditions () Bool (and cbac4c4d8_base_is_power_of_two
     (< cbac4c4d8_matched_quote_amount cbac4c4d8_matched_base_amount)))
(define-fun report_safety () Bool (=> (and (< 0 cbac4c4d8_matched_base_amount)
         (< 0 cbac4c4d8_matched_quote_amount))
    (not cbac4c4d8_legitimate_match_rejected)))
(define-fun report_effects () Bool (and (< 0 cbac4c4d8_matched_base_amount)
     (< 0 cbac4c4d8_matched_quote_amount)
     cbac4c4d8_legitimate_match_rejected
     (= 256 cbac4c4d8_impact_base_amount)
     (<= 1 cbac4c4d8_impact_quote_amount)
     (>= 255 cbac4c4d8_impact_quote_amount)
     cbac4c4d8_impact_revert_occurred
     (= 256 cbac4c4d8_impact_base_amount)
     (<= 1 cbac4c4d8_impact_quote_amount)
     (>= 255 cbac4c4d8_impact_quote_amount)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
