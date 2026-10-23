; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0aa389ac_launch_asset_amount_nonzero () Bool)
(declare-fun c0aa389ac_reentrancy_guard_present () Bool)
(declare-fun c0aa389ac_reentrancy_window_open () Bool)
(declare-fun c0aa389ac_reward_token_malicious () Bool)
(assert
 (= c0aa389ac_launch_asset_amount_nonzero c0aa389ac_launch_asset_amount_nonzero))
(assert
 (= c0aa389ac_reentrancy_guard_present c0aa389ac_reentrancy_guard_present))
(assert
 (= c0aa389ac_reentrancy_window_open c0aa389ac_reentrancy_window_open))
(assert
 (= c0aa389ac_reward_token_malicious c0aa389ac_reward_token_malicious))
(define-fun report_preconditions () Bool (and c0aa389ac_launch_asset_amount_nonzero c0aa389ac_reward_token_malicious))
(define-fun report_safety () Bool (=> c0aa389ac_reentrancy_window_open
    (=> c0aa389ac_reentrancy_window_open c0aa389ac_reentrancy_guard_present)))
(define-fun report_effects () Bool (and c0aa389ac_reentrancy_window_open
     c0aa389ac_reentrancy_window_open
     (not c0aa389ac_reentrancy_guard_present)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
