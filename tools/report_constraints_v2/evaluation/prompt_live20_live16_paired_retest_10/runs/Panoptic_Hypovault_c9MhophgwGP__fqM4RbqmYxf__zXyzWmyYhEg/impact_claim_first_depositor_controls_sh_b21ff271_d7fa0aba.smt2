; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c93954677_assets_exist_at_mint () Bool)
(declare-fun c93954677_first_depositor_share_control () Bool)
(declare-fun c93954677_supply_zero_at_start () Bool)
(declare-fun c93954677_total_assets_before_first_fulfillment () Int)
(declare-fun c93954677_total_supply_at_constructor () Int)
(assert
 (= c93954677_assets_exist_at_mint c93954677_assets_exist_at_mint))
(assert
 (= c93954677_first_depositor_share_control c93954677_first_depositor_share_control))
(assert
 (= c93954677_supply_zero_at_start c93954677_supply_zero_at_start))
(assert
 (= c93954677_total_assets_before_first_fulfillment c93954677_total_assets_before_first_fulfillment))
(assert
 (= c93954677_total_supply_at_constructor c93954677_total_supply_at_constructor))
(define-fun report_preconditions () Bool (and (= 1000000 c93954677_total_supply_at_constructor)
     (= 1 c93954677_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (and c93954677_supply_zero_at_start c93954677_assets_exist_at_mint)
    c93954677_assets_exist_at_mint))
(define-fun report_effects () Bool (and c93954677_first_depositor_share_control
     c93954677_first_depositor_share_control))
