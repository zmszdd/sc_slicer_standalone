; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9e61619a_hedge_asset_whitelisted () Bool)
(declare-fun c9e61619a_pm_mode_enabled () Bool)
(declare-fun c9e61619a_settlement_halted () Bool)
(declare-fun c9e61619a_supplied_slot_active () Bool)
(assert
 (= c9e61619a_hedge_asset_whitelisted c9e61619a_hedge_asset_whitelisted))
(assert
 (= c9e61619a_pm_mode_enabled c9e61619a_pm_mode_enabled))
(assert
 (= c9e61619a_settlement_halted c9e61619a_settlement_halted))
(assert
 (= c9e61619a_supplied_slot_active c9e61619a_supplied_slot_active))
(define-fun report_preconditions () Bool (and c9e61619a_pm_mode_enabled
     c9e61619a_hedge_asset_whitelisted
     (not c9e61619a_supplied_slot_active)))
(define-fun report_safety () Bool (=> c9e61619a_settlement_halted
    (=> (and c9e61619a_pm_mode_enabled
             c9e61619a_hedge_asset_whitelisted
             (not c9e61619a_supplied_slot_active))
        (not c9e61619a_settlement_halted))))
(define-fun report_effects () Bool (and c9e61619a_settlement_halted
     c9e61619a_pm_mode_enabled
     c9e61619a_hedge_asset_whitelisted
     (not c9e61619a_supplied_slot_active)
     (not (not c9e61619a_settlement_halted))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
