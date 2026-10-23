; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c881a9fea_emission_accounted_to_reward_flow () Bool)
(declare-fun c881a9fea_epoch_emission_minted () Bool)
(declare-fun c881a9fea_protocol_level_loss_occurs () Bool)
(declare-fun c881a9fea_total_weight_zero_before_distribute () Bool)
(assert
 (= c881a9fea_emission_accounted_to_reward_flow c881a9fea_emission_accounted_to_reward_flow))
(assert
 (= c881a9fea_epoch_emission_minted c881a9fea_epoch_emission_minted))
(assert
 (= c881a9fea_protocol_level_loss_occurs c881a9fea_protocol_level_loss_occurs))
(assert
 (= c881a9fea_total_weight_zero_before_distribute c881a9fea_total_weight_zero_before_distribute))
(define-fun report_preconditions () Bool c881a9fea_total_weight_zero_before_distribute)
(define-fun report_safety () Bool (=> c881a9fea_protocol_level_loss_occurs
    (=> c881a9fea_epoch_emission_minted
        c881a9fea_emission_accounted_to_reward_flow)))
(define-fun report_effects () Bool (and c881a9fea_protocol_level_loss_occurs
     c881a9fea_epoch_emission_minted
     (not c881a9fea_emission_accounted_to_reward_flow)))
