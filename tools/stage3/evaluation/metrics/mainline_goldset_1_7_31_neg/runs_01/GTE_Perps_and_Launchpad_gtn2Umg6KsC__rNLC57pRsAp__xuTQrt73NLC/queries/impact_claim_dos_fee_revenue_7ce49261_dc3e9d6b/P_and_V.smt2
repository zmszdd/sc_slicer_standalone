; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cad1aaf43_current_launchpad_lp_vault () ReportAddress)
(declare-fun cad1aaf43_factory_lp_fixed_at_construction () Bool)
(declare-fun cad1aaf43_fee_revenue_dos_for_subsequent_markets () Bool)
(declare-fun cad1aaf43_pair_launchpad_lp_config () ReportAddress)
(declare-fun cad1aaf43_vault_address_updated_post_deploy () Bool)
(assert
 (= cad1aaf43_current_launchpad_lp_vault cad1aaf43_current_launchpad_lp_vault))
(assert
 (= cad1aaf43_factory_lp_fixed_at_construction cad1aaf43_factory_lp_fixed_at_construction))
(assert
 (= cad1aaf43_fee_revenue_dos_for_subsequent_markets cad1aaf43_fee_revenue_dos_for_subsequent_markets))
(assert
 (= cad1aaf43_pair_launchpad_lp_config cad1aaf43_pair_launchpad_lp_config))
(assert
 (= cad1aaf43_vault_address_updated_post_deploy cad1aaf43_vault_address_updated_post_deploy))
(define-fun report_preconditions () Bool (and cad1aaf43_vault_address_updated_post_deploy
     cad1aaf43_factory_lp_fixed_at_construction))
(define-fun report_safety () Bool (=> cad1aaf43_vault_address_updated_post_deploy
    (= cad1aaf43_pair_launchpad_lp_config cad1aaf43_current_launchpad_lp_vault)))
(define-fun report_effects () Bool (and cad1aaf43_vault_address_updated_post_deploy
     (not (= cad1aaf43_pair_launchpad_lp_config
             cad1aaf43_current_launchpad_lp_vault))
     cad1aaf43_fee_revenue_dos_for_subsequent_markets
     cad1aaf43_fee_revenue_dos_for_subsequent_markets))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
