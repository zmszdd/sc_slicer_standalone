; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c84d2c6a4_factory_lp_fixed () Bool)
(declare-fun c84d2c6a4_fees_lost_occurred () Bool)
(declare-fun c84d2c6a4_launchpad_lp_vault_address () ReportAddress)
(declare-fun c84d2c6a4_lp_vault_updatable () Bool)
(declare-fun c84d2c6a4_pair_embedded_lp_address () ReportAddress)
(assert
 (= c84d2c6a4_factory_lp_fixed c84d2c6a4_factory_lp_fixed))
(assert
 (= c84d2c6a4_fees_lost_occurred c84d2c6a4_fees_lost_occurred))
(assert
 (= c84d2c6a4_launchpad_lp_vault_address c84d2c6a4_launchpad_lp_vault_address))
(assert
 (= c84d2c6a4_lp_vault_updatable c84d2c6a4_lp_vault_updatable))
(assert
 (= c84d2c6a4_pair_embedded_lp_address c84d2c6a4_pair_embedded_lp_address))
(define-fun report_preconditions () Bool (and c84d2c6a4_lp_vault_updatable c84d2c6a4_factory_lp_fixed))
(define-fun report_safety () Bool (=> c84d2c6a4_lp_vault_updatable
    (= c84d2c6a4_launchpad_lp_vault_address c84d2c6a4_pair_embedded_lp_address)))
(define-fun report_effects () Bool (and c84d2c6a4_lp_vault_updatable
     (not (= c84d2c6a4_launchpad_lp_vault_address
             c84d2c6a4_pair_embedded_lp_address))
     c84d2c6a4_fees_lost_occurred
     c84d2c6a4_fees_lost_occurred))
