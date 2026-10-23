; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2831c10d_launch_asset_amount_nonzero () Bool)
(declare-fun c2831c10d_monetary_extraction_occurs () Bool)
(declare-fun c2831c10d_reentry_during_transferfrom () Bool)
(declare-fun c2831c10d_reward_token_malicious () Bool)
(assert
 (= c2831c10d_launch_asset_amount_nonzero c2831c10d_launch_asset_amount_nonzero))
(assert
 (= c2831c10d_monetary_extraction_occurs c2831c10d_monetary_extraction_occurs))
(assert
 (= c2831c10d_reentry_during_transferfrom c2831c10d_reentry_during_transferfrom))
(assert
 (= c2831c10d_reward_token_malicious c2831c10d_reward_token_malicious))
(define-fun report_preconditions () Bool (and c2831c10d_launch_asset_amount_nonzero c2831c10d_reward_token_malicious))
(define-fun report_safety () Bool (=> c2831c10d_monetary_extraction_occurs
    (=> (and c2831c10d_launch_asset_amount_nonzero
             c2831c10d_reward_token_malicious)
        (not c2831c10d_reentry_during_transferfrom))))
(define-fun report_effects () Bool (and c2831c10d_monetary_extraction_occurs
     c2831c10d_launch_asset_amount_nonzero
     c2831c10d_reward_token_malicious
     (not (not c2831c10d_reentry_during_transferfrom))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
