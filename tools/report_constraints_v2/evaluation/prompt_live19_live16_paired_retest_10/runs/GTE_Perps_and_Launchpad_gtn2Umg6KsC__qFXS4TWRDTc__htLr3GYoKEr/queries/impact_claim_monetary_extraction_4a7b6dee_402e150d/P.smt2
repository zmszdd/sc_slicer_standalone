; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd6d5ee43_launch_asset_amount_nonzero () Bool)
(declare-fun cd6d5ee43_monetary_extraction_occurred () Bool)
(declare-fun cd6d5ee43_reentrancy_guard_active () Bool)
(declare-fun cd6d5ee43_reward_token_malicious () Bool)
(assert
 (= cd6d5ee43_launch_asset_amount_nonzero cd6d5ee43_launch_asset_amount_nonzero))
(assert
 (= cd6d5ee43_monetary_extraction_occurred cd6d5ee43_monetary_extraction_occurred))
(assert
 (= cd6d5ee43_reentrancy_guard_active cd6d5ee43_reentrancy_guard_active))
(assert
 (= cd6d5ee43_reward_token_malicious cd6d5ee43_reward_token_malicious))
(define-fun report_preconditions () Bool (and cd6d5ee43_launch_asset_amount_nonzero cd6d5ee43_reward_token_malicious))
(define-fun report_safety () Bool (=> cd6d5ee43_monetary_extraction_occurred
    (=> cd6d5ee43_monetary_extraction_occurred
        cd6d5ee43_reentrancy_guard_active)))
(define-fun report_effects () Bool (and cd6d5ee43_monetary_extraction_occurred
     cd6d5ee43_monetary_extraction_occurred
     (not cd6d5ee43_reentrancy_guard_active)))
(assert report_preconditions)
(check-sat)
(get-model)
