; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun ccc9328b4_factory_lp_fixed_at_construction () Bool)
(declare-fun ccc9328b4_fee_revenue_dos_occurred () Bool)
(declare-fun ccc9328b4_launchpad_lp_vault_address () ReportAddress)
(declare-fun ccc9328b4_lp_vault_updated_post_deploy () Bool)
(declare-fun ccc9328b4_pair_embedded_lp_address () ReportAddress)
(assert
 (= ccc9328b4_factory_lp_fixed_at_construction ccc9328b4_factory_lp_fixed_at_construction))
(assert
 (= ccc9328b4_fee_revenue_dos_occurred ccc9328b4_fee_revenue_dos_occurred))
(assert
 (= ccc9328b4_launchpad_lp_vault_address ccc9328b4_launchpad_lp_vault_address))
(assert
 (= ccc9328b4_lp_vault_updated_post_deploy ccc9328b4_lp_vault_updated_post_deploy))
(assert
 (= ccc9328b4_pair_embedded_lp_address ccc9328b4_pair_embedded_lp_address))
(define-fun report_preconditions () Bool (and ccc9328b4_lp_vault_updated_post_deploy
     ccc9328b4_factory_lp_fixed_at_construction))
(define-fun report_safety () Bool (=> ccc9328b4_lp_vault_updated_post_deploy
    (= ccc9328b4_launchpad_lp_vault_address ccc9328b4_pair_embedded_lp_address)))
(define-fun report_effects () Bool (and ccc9328b4_lp_vault_updated_post_deploy
     (not (= ccc9328b4_launchpad_lp_vault_address
             ccc9328b4_pair_embedded_lp_address))
     ccc9328b4_fee_revenue_dos_occurred
     ccc9328b4_fee_revenue_dos_occurred))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
