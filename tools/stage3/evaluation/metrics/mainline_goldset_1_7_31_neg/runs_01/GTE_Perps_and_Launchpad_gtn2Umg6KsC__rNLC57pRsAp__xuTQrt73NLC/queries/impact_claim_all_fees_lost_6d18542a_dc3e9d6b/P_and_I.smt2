; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c16b39b6e_factory_lp_fixed_at_construction () Bool)
(declare-fun c16b39b6e_fees_lost () Bool)
(declare-fun c16b39b6e_lp_vault_address_updatable () Bool)
(declare-fun c16b39b6e_pair_config_rotatable () Bool)
(declare-fun c16b39b6e_pair_tracks_current_vault () Bool)
(assert
 (= c16b39b6e_factory_lp_fixed_at_construction c16b39b6e_factory_lp_fixed_at_construction))
(assert
 (= c16b39b6e_fees_lost c16b39b6e_fees_lost))
(assert
 (= c16b39b6e_lp_vault_address_updatable c16b39b6e_lp_vault_address_updatable))
(assert
 (= c16b39b6e_pair_config_rotatable c16b39b6e_pair_config_rotatable))
(assert
 (= c16b39b6e_pair_tracks_current_vault c16b39b6e_pair_tracks_current_vault))
(define-fun report_preconditions () Bool (and c16b39b6e_lp_vault_address_updatable
     c16b39b6e_factory_lp_fixed_at_construction
     c16b39b6e_pair_config_rotatable))
(define-fun report_safety () Bool (= c16b39b6e_pair_tracks_current_vault c16b39b6e_pair_config_rotatable))
(define-fun report_effects () Bool (and c16b39b6e_pair_config_rotatable
     (not (= c16b39b6e_pair_tracks_current_vault
             c16b39b6e_pair_config_rotatable))
     c16b39b6e_fees_lost
     c16b39b6e_fees_lost))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
