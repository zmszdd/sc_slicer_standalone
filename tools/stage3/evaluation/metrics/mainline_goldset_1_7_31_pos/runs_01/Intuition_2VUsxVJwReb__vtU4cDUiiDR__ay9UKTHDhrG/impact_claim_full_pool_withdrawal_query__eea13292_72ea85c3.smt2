; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7f14c050_first_deposit_assets () Int)
(declare-fun c7f14c050_first_deposit_shares () Int)
(declare-fun c7f14c050_full_exit_preview_unavailable () Bool)
(declare-fun c7f14c050_offset18_initialized () Int)
(declare-fun c7f14c050_preview_withdraw_reverts () Bool)
(declare-fun c7f14c050_preview_withdraw_valid_inputs () Bool)
(declare-fun c7f14c050_slope18_initialized () Int)
(assert
 (= c7f14c050_first_deposit_assets c7f14c050_first_deposit_assets))
(assert
 (= c7f14c050_first_deposit_shares c7f14c050_first_deposit_shares))
(assert
 (= c7f14c050_full_exit_preview_unavailable c7f14c050_full_exit_preview_unavailable))
(assert
 (= c7f14c050_offset18_initialized c7f14c050_offset18_initialized))
(assert
 (= c7f14c050_preview_withdraw_reverts c7f14c050_preview_withdraw_reverts))
(assert
 (= c7f14c050_preview_withdraw_valid_inputs c7f14c050_preview_withdraw_valid_inputs))
(assert
 (= c7f14c050_slope18_initialized c7f14c050_slope18_initialized))
(define-fun report_preconditions () Bool (and (= 0 c7f14c050_offset18_initialized)
     (= 2000000000000000000 c7f14c050_slope18_initialized)
     (= 2 c7f14c050_first_deposit_assets)
     (= 1414213562 c7f14c050_first_deposit_shares)
     c7f14c050_preview_withdraw_valid_inputs))
(define-fun report_safety () Bool (not c7f14c050_preview_withdraw_reverts))
(define-fun report_effects () Bool (and c7f14c050_preview_withdraw_valid_inputs
     c7f14c050_preview_withdraw_reverts
     c7f14c050_preview_withdraw_reverts
     c7f14c050_full_exit_preview_unavailable
     c7f14c050_full_exit_preview_unavailable))
