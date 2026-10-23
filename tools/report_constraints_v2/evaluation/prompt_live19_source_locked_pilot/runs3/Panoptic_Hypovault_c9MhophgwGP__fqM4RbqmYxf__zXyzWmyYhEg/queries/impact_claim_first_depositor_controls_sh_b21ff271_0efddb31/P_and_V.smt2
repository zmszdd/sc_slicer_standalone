; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb12d3f09_first_depositor_share_control () Bool)
(declare-fun cb12d3f09_shares_minted_only_when_assets_exist () Bool)
(declare-fun cb12d3f09_supply_starts_at_zero () Bool)
(declare-fun cb12d3f09_total_assets_before_first_fulfillment () Int)
(declare-fun cb12d3f09_total_supply_at_construction () Int)
(declare-fun cb12d3f09_vault_underlying_assets_at_construction () Int)
(assert
 (= cb12d3f09_first_depositor_share_control cb12d3f09_first_depositor_share_control))
(assert
 (= cb12d3f09_shares_minted_only_when_assets_exist cb12d3f09_shares_minted_only_when_assets_exist))
(assert
 (= cb12d3f09_supply_starts_at_zero cb12d3f09_supply_starts_at_zero))
(assert
 (= cb12d3f09_total_assets_before_first_fulfillment cb12d3f09_total_assets_before_first_fulfillment))
(assert
 (= cb12d3f09_total_supply_at_construction cb12d3f09_total_supply_at_construction))
(assert
 (= cb12d3f09_vault_underlying_assets_at_construction cb12d3f09_vault_underlying_assets_at_construction))
(define-fun report_preconditions () Bool (and (= 1000000 cb12d3f09_total_supply_at_construction)
     (= 0 cb12d3f09_vault_underlying_assets_at_construction)
     (= 1 cb12d3f09_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> cb12d3f09_supply_starts_at_zero
    cb12d3f09_shares_minted_only_when_assets_exist))
(define-fun report_effects () Bool (and cb12d3f09_first_depositor_share_control
     cb12d3f09_first_depositor_share_control))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
