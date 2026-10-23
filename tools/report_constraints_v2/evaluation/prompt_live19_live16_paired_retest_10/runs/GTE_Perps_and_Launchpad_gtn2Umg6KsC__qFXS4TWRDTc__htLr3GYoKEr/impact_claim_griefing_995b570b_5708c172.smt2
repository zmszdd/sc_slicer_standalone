; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfd65eca4_griefing_occurs () Bool)
(declare-fun cfd65eca4_launch_asset_amount_nonzero () Bool)
(declare-fun cfd65eca4_reentry_during_transferfrom () Bool)
(declare-fun cfd65eca4_reward_token_malicious () Bool)
(assert
 (= cfd65eca4_griefing_occurs cfd65eca4_griefing_occurs))
(assert
 (= cfd65eca4_launch_asset_amount_nonzero cfd65eca4_launch_asset_amount_nonzero))
(assert
 (= cfd65eca4_reentry_during_transferfrom cfd65eca4_reentry_during_transferfrom))
(assert
 (= cfd65eca4_reward_token_malicious cfd65eca4_reward_token_malicious))
(define-fun report_preconditions () Bool (and cfd65eca4_launch_asset_amount_nonzero cfd65eca4_reward_token_malicious))
(define-fun report_safety () Bool (=> cfd65eca4_griefing_occurs
    (=> (and cfd65eca4_launch_asset_amount_nonzero
             cfd65eca4_reward_token_malicious)
        (not cfd65eca4_reentry_during_transferfrom))))
(define-fun report_effects () Bool (and cfd65eca4_griefing_occurs
     cfd65eca4_launch_asset_amount_nonzero
     cfd65eca4_reward_token_malicious
     (not (not cfd65eca4_reentry_during_transferfrom))))
