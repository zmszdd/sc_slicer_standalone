; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c9ae57726_add_liquidity_recipient_vault () ReportAddress)
(declare-fun c9ae57726_distributor_rewards_accrued () Bool)
(declare-fun c9ae57726_factory_lp_fixed_at_construction () Bool)
(declare-fun c9ae57726_lp_vault_address_updatable () Bool)
(declare-fun c9ae57726_pair_embedded_vault () ReportAddress)
(assert
 (= c9ae57726_add_liquidity_recipient_vault c9ae57726_add_liquidity_recipient_vault))
(assert
 (= c9ae57726_distributor_rewards_accrued c9ae57726_distributor_rewards_accrued))
(assert
 (= c9ae57726_factory_lp_fixed_at_construction c9ae57726_factory_lp_fixed_at_construction))
(assert
 (= c9ae57726_lp_vault_address_updatable c9ae57726_lp_vault_address_updatable))
(assert
 (= c9ae57726_pair_embedded_vault c9ae57726_pair_embedded_vault))
(define-fun report_preconditions () Bool (and c9ae57726_lp_vault_address_updatable
     c9ae57726_factory_lp_fixed_at_construction))
(define-fun report_safety () Bool (=> c9ae57726_factory_lp_fixed_at_construction
    (= c9ae57726_add_liquidity_recipient_vault c9ae57726_pair_embedded_vault)))
(define-fun report_effects () Bool (and c9ae57726_factory_lp_fixed_at_construction
     (not (= c9ae57726_add_liquidity_recipient_vault
             c9ae57726_pair_embedded_vault))
     (not c9ae57726_distributor_rewards_accrued)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
