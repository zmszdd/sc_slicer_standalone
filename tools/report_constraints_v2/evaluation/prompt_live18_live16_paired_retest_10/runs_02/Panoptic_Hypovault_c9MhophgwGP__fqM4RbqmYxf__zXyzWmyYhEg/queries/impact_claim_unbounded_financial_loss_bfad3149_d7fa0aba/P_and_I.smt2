; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c925cf983_total_assets_before_first_fulfilment () Int)
(declare-fun c925cf983_total_supply_at_construction () Int)
(declare-fun c925cf983_unbounded_loss_occurred () Bool)
(declare-fun c925cf983_vault_assets_at_construction () Int)
(declare-fun c925cf983_zero_assets () Int)
(declare-fun c925cf983_zero_shares () Int)
(assert
 (= c925cf983_total_assets_before_first_fulfilment c925cf983_total_assets_before_first_fulfilment))
(assert
 (= c925cf983_total_supply_at_construction c925cf983_total_supply_at_construction))
(assert
 (= c925cf983_unbounded_loss_occurred c925cf983_unbounded_loss_occurred))
(assert
 (= c925cf983_vault_assets_at_construction c925cf983_vault_assets_at_construction))
(assert
 (= c925cf983_zero_assets c925cf983_zero_assets))
(assert
 (= c925cf983_zero_shares c925cf983_zero_shares))
(define-fun report_preconditions () Bool (and (= 1000000 c925cf983_total_supply_at_construction)
     (= 0 c925cf983_vault_assets_at_construction)
     (= 1 c925cf983_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> c925cf983_unbounded_loss_occurred
    (=> (= c925cf983_total_assets_before_first_fulfilment c925cf983_zero_assets)
        (= c925cf983_total_supply_at_construction c925cf983_zero_shares))))
(define-fun report_effects () Bool (and c925cf983_unbounded_loss_occurred
     (= c925cf983_total_assets_before_first_fulfilment c925cf983_zero_assets)
     (not (= c925cf983_total_supply_at_construction c925cf983_zero_shares))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
