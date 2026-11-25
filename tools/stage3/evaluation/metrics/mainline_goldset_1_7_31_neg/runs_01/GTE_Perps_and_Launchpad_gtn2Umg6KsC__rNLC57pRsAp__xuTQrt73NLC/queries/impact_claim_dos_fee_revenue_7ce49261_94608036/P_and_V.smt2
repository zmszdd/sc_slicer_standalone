; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c756b340c_factory_lp_fixed_at_construction () Bool)
(declare-fun c756b340c_fee_computation_at_use_time () Bool)
(declare-fun c756b340c_fee_revenue_dos_scope () Bool)
(declare-fun c756b340c_launchpad_current_lp_vault () ReportAddress)
(declare-fun c756b340c_lp_vault_address_updatable () Bool)
(declare-fun c756b340c_pair_queried_lp_vault () ReportAddress)
(assert
 (= c756b340c_factory_lp_fixed_at_construction c756b340c_factory_lp_fixed_at_construction))
(assert
 (= c756b340c_fee_computation_at_use_time c756b340c_fee_computation_at_use_time))
(assert
 (= c756b340c_fee_revenue_dos_scope c756b340c_fee_revenue_dos_scope))
(assert
 (= c756b340c_launchpad_current_lp_vault c756b340c_launchpad_current_lp_vault))
(assert
 (= c756b340c_lp_vault_address_updatable c756b340c_lp_vault_address_updatable))
(assert
 (= c756b340c_pair_queried_lp_vault c756b340c_pair_queried_lp_vault))
(define-fun report_preconditions () Bool (and c756b340c_lp_vault_address_updatable
     c756b340c_factory_lp_fixed_at_construction
     c756b340c_fee_computation_at_use_time))
(define-fun report_safety () Bool (= c756b340c_pair_queried_lp_vault c756b340c_launchpad_current_lp_vault))
(define-fun report_effects () Bool (and c756b340c_fee_computation_at_use_time
     (not (= c756b340c_pair_queried_lp_vault
             c756b340c_launchpad_current_lp_vault))
     c756b340c_fee_revenue_dos_scope
     c756b340c_fee_revenue_dos_scope))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
