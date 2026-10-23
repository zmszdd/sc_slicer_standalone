; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf1516fa_supply_starts_at_zero () Bool)
(declare-fun cbf1516fa_total_assets_before_first_fulfillment () Int)
(declare-fun cbf1516fa_total_supply_at_bootstrap () Int)
(declare-fun cbf1516fa_withdrawal_burns_shares_for_tiny_assets () Bool)
(assert
 (= cbf1516fa_supply_starts_at_zero cbf1516fa_supply_starts_at_zero))
(assert
 (= cbf1516fa_total_assets_before_first_fulfillment cbf1516fa_total_assets_before_first_fulfillment))
(assert
 (= cbf1516fa_total_supply_at_bootstrap cbf1516fa_total_supply_at_bootstrap))
(assert
 (= cbf1516fa_withdrawal_burns_shares_for_tiny_assets cbf1516fa_withdrawal_burns_shares_for_tiny_assets))
(define-fun report_preconditions () Bool (and (= 1000000 cbf1516fa_total_supply_at_bootstrap)
     (= 1 cbf1516fa_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> cbf1516fa_supply_starts_at_zero (= 0 cbf1516fa_total_supply_at_bootstrap)))
(define-fun report_effects () Bool cbf1516fa_withdrawal_burns_shares_for_tiny_assets)
