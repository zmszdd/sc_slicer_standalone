; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cdb8273e2_current_launchpad_lp_vault () ReportAddress)
(declare-fun cdb8273e2_factory_lp_fixed_at_construction () Bool)
(declare-fun cdb8273e2_lp_vault_address_updatable () Bool)
(declare-fun cdb8273e2_pair_queried_lp_vault () ReportAddress)
(declare-fun cdb8273e2_rewards_accrued () Bool)
(assert
 (= cdb8273e2_current_launchpad_lp_vault cdb8273e2_current_launchpad_lp_vault))
(assert
 (= cdb8273e2_factory_lp_fixed_at_construction cdb8273e2_factory_lp_fixed_at_construction))
(assert
 (= cdb8273e2_lp_vault_address_updatable cdb8273e2_lp_vault_address_updatable))
(assert
 (= cdb8273e2_pair_queried_lp_vault cdb8273e2_pair_queried_lp_vault))
(assert
 (= cdb8273e2_rewards_accrued cdb8273e2_rewards_accrued))
(define-fun report_preconditions () Bool (and cdb8273e2_lp_vault_address_updatable
     cdb8273e2_factory_lp_fixed_at_construction))
(define-fun report_safety () Bool (=> cdb8273e2_lp_vault_address_updatable
    (= cdb8273e2_pair_queried_lp_vault cdb8273e2_current_launchpad_lp_vault)))
(define-fun report_effects () Bool (and cdb8273e2_lp_vault_address_updatable
     (not (= cdb8273e2_pair_queried_lp_vault
             cdb8273e2_current_launchpad_lp_vault))
     (not cdb8273e2_rewards_accrued)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
