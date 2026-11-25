; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1d7867d9_factory_lp_fixed_at_construction () Bool)
(declare-fun c1d7867d9_lp_vault_address_updatable () Bool)
(declare-fun c1d7867d9_pair_config_rotatable () Bool)
(declare-fun c1d7867d9_pair_tracks_current_vault () Bool)
(declare-fun c1d7867d9_rewards_accrue () Bool)
(assert
 (= c1d7867d9_factory_lp_fixed_at_construction c1d7867d9_factory_lp_fixed_at_construction))
(assert
 (= c1d7867d9_lp_vault_address_updatable c1d7867d9_lp_vault_address_updatable))
(assert
 (= c1d7867d9_pair_config_rotatable c1d7867d9_pair_config_rotatable))
(assert
 (= c1d7867d9_pair_tracks_current_vault c1d7867d9_pair_tracks_current_vault))
(assert
 (= c1d7867d9_rewards_accrue c1d7867d9_rewards_accrue))
(define-fun report_preconditions () Bool (and c1d7867d9_lp_vault_address_updatable
     c1d7867d9_factory_lp_fixed_at_construction
     c1d7867d9_pair_config_rotatable))
(define-fun report_safety () Bool (= c1d7867d9_pair_tracks_current_vault c1d7867d9_pair_config_rotatable))
(define-fun report_effects () Bool (and c1d7867d9_pair_config_rotatable
     (not (= c1d7867d9_pair_tracks_current_vault
             c1d7867d9_pair_config_rotatable))
     (not c1d7867d9_rewards_accrue)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
