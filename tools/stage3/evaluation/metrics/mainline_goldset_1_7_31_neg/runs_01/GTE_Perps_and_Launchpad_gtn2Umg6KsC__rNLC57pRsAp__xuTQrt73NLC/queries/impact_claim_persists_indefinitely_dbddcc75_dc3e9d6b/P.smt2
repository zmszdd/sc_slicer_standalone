; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c19228e4b_current_lp_vault () ReportAddress)
(declare-fun c19228e4b_factory_lp_fixed_at_construction () Bool)
(declare-fun c19228e4b_launchpad_lp_vault_updatable () Bool)
(declare-fun c19228e4b_launchpad_lp_vault_updated () Bool)
(declare-fun c19228e4b_misconfiguration_persists_indefinitely () Bool)
(declare-fun c19228e4b_pair_cached_lp_vault () ReportAddress)
(assert
 (= c19228e4b_current_lp_vault c19228e4b_current_lp_vault))
(assert
 (= c19228e4b_factory_lp_fixed_at_construction c19228e4b_factory_lp_fixed_at_construction))
(assert
 (= c19228e4b_launchpad_lp_vault_updatable c19228e4b_launchpad_lp_vault_updatable))
(assert
 (= c19228e4b_launchpad_lp_vault_updated c19228e4b_launchpad_lp_vault_updated))
(assert
 (= c19228e4b_misconfiguration_persists_indefinitely c19228e4b_misconfiguration_persists_indefinitely))
(assert
 (= c19228e4b_pair_cached_lp_vault c19228e4b_pair_cached_lp_vault))
(define-fun report_preconditions () Bool (and c19228e4b_launchpad_lp_vault_updatable
     c19228e4b_factory_lp_fixed_at_construction))
(define-fun report_safety () Bool (=> c19228e4b_launchpad_lp_vault_updated
    (= c19228e4b_pair_cached_lp_vault c19228e4b_current_lp_vault)))
(define-fun report_effects () Bool (and c19228e4b_launchpad_lp_vault_updated
     (not (= c19228e4b_pair_cached_lp_vault c19228e4b_current_lp_vault))
     c19228e4b_misconfiguration_persists_indefinitely
     c19228e4b_misconfiguration_persists_indefinitely))
(assert report_preconditions)
(check-sat)
(get-model)
