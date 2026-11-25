; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbdeab9b3_computed_fee_share_is_zero () Bool)
(declare-fun cbdeab9b3_factory_lp_fixed_at_construction () Bool)
(declare-fun cbdeab9b3_lp_vault_updated_post_deploy () Bool)
(declare-fun cbdeab9b3_market_graduates_after_vault_update () Bool)
(declare-fun cbdeab9b3_pair_queries_current_vault_at_use_time () Bool)
(declare-fun cbdeab9b3_pair_uses_stale_vault_config () Bool)
(assert
 (= cbdeab9b3_computed_fee_share_is_zero cbdeab9b3_computed_fee_share_is_zero))
(assert
 (= cbdeab9b3_factory_lp_fixed_at_construction cbdeab9b3_factory_lp_fixed_at_construction))
(assert
 (= cbdeab9b3_lp_vault_updated_post_deploy cbdeab9b3_lp_vault_updated_post_deploy))
(assert
 (= cbdeab9b3_market_graduates_after_vault_update cbdeab9b3_market_graduates_after_vault_update))
(assert
 (= cbdeab9b3_pair_queries_current_vault_at_use_time cbdeab9b3_pair_queries_current_vault_at_use_time))
(assert
 (= cbdeab9b3_pair_uses_stale_vault_config cbdeab9b3_pair_uses_stale_vault_config))
(define-fun report_preconditions () Bool (and cbdeab9b3_lp_vault_updated_post_deploy
     cbdeab9b3_factory_lp_fixed_at_construction
     cbdeab9b3_market_graduates_after_vault_update))
(define-fun report_safety () Bool (= cbdeab9b3_pair_uses_stale_vault_config
   cbdeab9b3_pair_queries_current_vault_at_use_time))
(define-fun report_effects () Bool (and cbdeab9b3_market_graduates_after_vault_update
     (not (= cbdeab9b3_pair_uses_stale_vault_config
             cbdeab9b3_pair_queries_current_vault_at_use_time))
     cbdeab9b3_market_graduates_after_vault_update
     cbdeab9b3_computed_fee_share_is_zero
     cbdeab9b3_market_graduates_after_vault_update))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
