; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cba6fb966_griefing_occurs () Bool)
(declare-fun cba6fb966_launch_asset_amount_nonzero () Bool)
(declare-fun cba6fb966_reentrancy_guard_active () Bool)
(declare-fun cba6fb966_reward_token_malicious () Bool)
(assert
 (= cba6fb966_griefing_occurs cba6fb966_griefing_occurs))
(assert
 (= cba6fb966_launch_asset_amount_nonzero cba6fb966_launch_asset_amount_nonzero))
(assert
 (= cba6fb966_reentrancy_guard_active cba6fb966_reentrancy_guard_active))
(assert
 (= cba6fb966_reward_token_malicious cba6fb966_reward_token_malicious))
(define-fun report_preconditions () Bool (and cba6fb966_launch_asset_amount_nonzero cba6fb966_reward_token_malicious))
(define-fun report_safety () Bool (=> cba6fb966_griefing_occurs
    (=> cba6fb966_griefing_occurs cba6fb966_reentrancy_guard_active)))
(define-fun report_effects () Bool (and cba6fb966_griefing_occurs
     cba6fb966_griefing_occurs
     (not cba6fb966_reentrancy_guard_active)))
