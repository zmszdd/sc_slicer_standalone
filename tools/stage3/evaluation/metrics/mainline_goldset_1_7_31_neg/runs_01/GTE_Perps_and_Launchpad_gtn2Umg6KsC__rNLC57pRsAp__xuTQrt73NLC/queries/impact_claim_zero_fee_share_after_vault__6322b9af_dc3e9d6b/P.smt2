; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c8558a86c_current_vault () ReportAddress)
(declare-fun c8558a86c_factory_lp_fixed_at_construction () Bool)
(declare-fun c8558a86c_fee_share_zero_after_vault_update () Bool)
(declare-fun c8558a86c_market_graduates_after_vault_update () Bool)
(declare-fun c8558a86c_pair_config_rotatable () Bool)
(declare-fun c8558a86c_pair_configured_vault () ReportAddress)
(declare-fun c8558a86c_vault_address_updatable () Bool)
(assert
 (= c8558a86c_current_vault c8558a86c_current_vault))
(assert
 (= c8558a86c_factory_lp_fixed_at_construction c8558a86c_factory_lp_fixed_at_construction))
(assert
 (= c8558a86c_fee_share_zero_after_vault_update c8558a86c_fee_share_zero_after_vault_update))
(assert
 (= c8558a86c_market_graduates_after_vault_update c8558a86c_market_graduates_after_vault_update))
(assert
 (= c8558a86c_pair_config_rotatable c8558a86c_pair_config_rotatable))
(assert
 (= c8558a86c_pair_configured_vault c8558a86c_pair_configured_vault))
(assert
 (= c8558a86c_vault_address_updatable c8558a86c_vault_address_updatable))
(define-fun report_preconditions () Bool (and c8558a86c_vault_address_updatable
     c8558a86c_factory_lp_fixed_at_construction
     c8558a86c_pair_config_rotatable))
(define-fun report_safety () Bool (= c8558a86c_pair_configured_vault c8558a86c_current_vault))
(define-fun report_effects () Bool (and c8558a86c_pair_config_rotatable
     (not (= c8558a86c_pair_configured_vault c8558a86c_current_vault))
     c8558a86c_fee_share_zero_after_vault_update
     c8558a86c_market_graduates_after_vault_update))
(assert report_preconditions)
(check-sat)
(get-model)
