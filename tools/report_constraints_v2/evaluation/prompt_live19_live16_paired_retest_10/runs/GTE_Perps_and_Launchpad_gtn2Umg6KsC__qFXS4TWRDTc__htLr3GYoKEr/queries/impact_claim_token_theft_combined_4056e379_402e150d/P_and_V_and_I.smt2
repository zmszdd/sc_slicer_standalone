; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca9e70612_launch_asset_amount_nonzero () Bool)
(declare-fun ca9e70612_reentrancy_guard_present () Bool)
(declare-fun ca9e70612_reward_token_malicious () Bool)
(declare-fun ca9e70612_tokens_stolen () Bool)
(assert
 (= ca9e70612_launch_asset_amount_nonzero ca9e70612_launch_asset_amount_nonzero))
(assert
 (= ca9e70612_reentrancy_guard_present ca9e70612_reentrancy_guard_present))
(assert
 (= ca9e70612_reward_token_malicious ca9e70612_reward_token_malicious))
(assert
 (= ca9e70612_tokens_stolen ca9e70612_tokens_stolen))
(define-fun report_preconditions () Bool (and ca9e70612_launch_asset_amount_nonzero ca9e70612_reward_token_malicious))
(define-fun report_safety () Bool (=> ca9e70612_tokens_stolen
    (=> ca9e70612_tokens_stolen ca9e70612_reentrancy_guard_present)))
(define-fun report_effects () Bool (and ca9e70612_tokens_stolen
     ca9e70612_tokens_stolen
     (not ca9e70612_reentrancy_guard_present)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
