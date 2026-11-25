; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c3eaed1f9_add_liquidity_recipient_vault () ReportAddress)
(declare-fun c3eaed1f9_computed_fee_share () Int)
(declare-fun c3eaed1f9_factory_lp_fixed_at_construction () Bool)
(declare-fun c3eaed1f9_lp_vault_updatable () Bool)
(declare-fun c3eaed1f9_pair_embedded_vault () ReportAddress)
(declare-fun c3eaed1f9_pair_launchpad_lp_balance () Int)
(assert
 (= c3eaed1f9_add_liquidity_recipient_vault c3eaed1f9_add_liquidity_recipient_vault))
(assert
 (= c3eaed1f9_computed_fee_share c3eaed1f9_computed_fee_share))
(assert
 (= c3eaed1f9_factory_lp_fixed_at_construction c3eaed1f9_factory_lp_fixed_at_construction))
(assert
 (= c3eaed1f9_lp_vault_updatable c3eaed1f9_lp_vault_updatable))
(assert
 (= c3eaed1f9_pair_embedded_vault c3eaed1f9_pair_embedded_vault))
(assert
 (= c3eaed1f9_pair_launchpad_lp_balance c3eaed1f9_pair_launchpad_lp_balance))
(define-fun report_preconditions () Bool (and c3eaed1f9_lp_vault_updatable c3eaed1f9_factory_lp_fixed_at_construction))
(define-fun report_safety () Bool (=> c3eaed1f9_lp_vault_updatable
    (= c3eaed1f9_add_liquidity_recipient_vault c3eaed1f9_pair_embedded_vault)))
(define-fun report_effects () Bool (and c3eaed1f9_lp_vault_updatable
     (not (= c3eaed1f9_add_liquidity_recipient_vault
             c3eaed1f9_pair_embedded_vault))
     (and (= 0 c3eaed1f9_pair_launchpad_lp_balance)
          (= 0 c3eaed1f9_computed_fee_share))
     (and (= 0 c3eaed1f9_pair_launchpad_lp_balance)
          (= 0 c3eaed1f9_computed_fee_share))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
