; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun ccca8d5ae_add_rewards_pair_token () ReportAddress)
(declare-fun ccca8d5ae_configured_quote_asset () ReportAddress)
(declare-fun ccca8d5ae_fake_token_approved () Bool)
(declare-fun ccca8d5ae_pool_total_shares () Int)
(declare-fun ccca8d5ae_quote_claim_dos_active () Bool)
(assert
 (= ccca8d5ae_add_rewards_pair_token ccca8d5ae_add_rewards_pair_token))
(assert
 (= ccca8d5ae_configured_quote_asset ccca8d5ae_configured_quote_asset))
(assert
 (= ccca8d5ae_fake_token_approved ccca8d5ae_fake_token_approved))
(assert
 (= ccca8d5ae_pool_total_shares ccca8d5ae_pool_total_shares))
(assert
 (= ccca8d5ae_quote_claim_dos_active ccca8d5ae_quote_claim_dos_active))
(define-fun report_preconditions () Bool (and (< 0 ccca8d5ae_pool_total_shares) ccca8d5ae_fake_token_approved))
(define-fun report_safety () Bool (=> ccca8d5ae_fake_token_approved
    (= ccca8d5ae_add_rewards_pair_token ccca8d5ae_configured_quote_asset)))
(define-fun report_effects () Bool (and ccca8d5ae_fake_token_approved
     (not (= ccca8d5ae_add_rewards_pair_token ccca8d5ae_configured_quote_asset))
     ccca8d5ae_quote_claim_dos_active
     ccca8d5ae_quote_claim_dos_active))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
