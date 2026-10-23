; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6862442e_launch_asset_amount_nonzero () Bool)
(declare-fun c6862442e_reentry_during_transferfrom () Bool)
(declare-fun c6862442e_reward_token_malicious () Bool)
(declare-fun c6862442e_tokens_stolen () Bool)
(assert
 (= c6862442e_launch_asset_amount_nonzero c6862442e_launch_asset_amount_nonzero))
(assert
 (= c6862442e_reentry_during_transferfrom c6862442e_reentry_during_transferfrom))
(assert
 (= c6862442e_reward_token_malicious c6862442e_reward_token_malicious))
(assert
 (= c6862442e_tokens_stolen c6862442e_tokens_stolen))
(define-fun report_preconditions () Bool (and c6862442e_launch_asset_amount_nonzero c6862442e_reward_token_malicious))
(define-fun report_safety () Bool (=> c6862442e_tokens_stolen
    (=> (and c6862442e_launch_asset_amount_nonzero
             c6862442e_reward_token_malicious)
        (not c6862442e_reentry_during_transferfrom))))
(define-fun report_effects () Bool (and c6862442e_tokens_stolen
     c6862442e_launch_asset_amount_nonzero
     c6862442e_reward_token_malicious
     (not (not c6862442e_reentry_during_transferfrom))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
