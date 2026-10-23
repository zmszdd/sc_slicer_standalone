; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c61a0e823_hedge_asset_whitelisted () Bool)
(declare-fun c61a0e823_pm_mode_enabled () Bool)
(declare-fun c61a0e823_supplied_slot_active () Bool)
(declare-fun c61a0e823_surplus_check_halted () Bool)
(assert
 (= c61a0e823_hedge_asset_whitelisted c61a0e823_hedge_asset_whitelisted))
(assert
 (= c61a0e823_pm_mode_enabled c61a0e823_pm_mode_enabled))
(assert
 (= c61a0e823_supplied_slot_active c61a0e823_supplied_slot_active))
(assert
 (= c61a0e823_surplus_check_halted c61a0e823_surplus_check_halted))
(define-fun report_preconditions () Bool (and c61a0e823_pm_mode_enabled
     c61a0e823_hedge_asset_whitelisted
     (not c61a0e823_supplied_slot_active)))
(define-fun report_safety () Bool (=> (and c61a0e823_pm_mode_enabled
         c61a0e823_hedge_asset_whitelisted
         (not c61a0e823_supplied_slot_active))
    (not c61a0e823_surplus_check_halted)))
(define-fun report_effects () Bool (and c61a0e823_pm_mode_enabled
     c61a0e823_hedge_asset_whitelisted
     (not c61a0e823_supplied_slot_active)
     (not (not c61a0e823_surplus_check_halted))))
(assert report_preconditions)
(check-sat)
(get-model)
