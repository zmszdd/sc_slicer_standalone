; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdc6b3909_later_deposit_amount () Int)
(declare-fun cdc6b3909_minted_shares_for_later_deposit () Int)
(declare-fun cdc6b3909_precomputed_shares_minted () Bool)
(declare-fun cdc6b3909_shares_computed_from_pre_deposit_snapshot () Bool)
(declare-fun cdc6b3909_total_assets_before_deposit () Int)
(declare-fun cdc6b3909_total_supply_before_deposit () Int)
(assert
 (= cdc6b3909_later_deposit_amount cdc6b3909_later_deposit_amount))
(assert
 (= cdc6b3909_minted_shares_for_later_deposit cdc6b3909_minted_shares_for_later_deposit))
(assert
 (= cdc6b3909_precomputed_shares_minted cdc6b3909_precomputed_shares_minted))
(assert
 (= cdc6b3909_shares_computed_from_pre_deposit_snapshot cdc6b3909_shares_computed_from_pre_deposit_snapshot))
(assert
 (= cdc6b3909_total_assets_before_deposit cdc6b3909_total_assets_before_deposit))
(assert
 (= cdc6b3909_total_supply_before_deposit cdc6b3909_total_supply_before_deposit))
(define-fun report_preconditions () Bool (and (= 1 cdc6b3909_total_supply_before_deposit)
     (= 1 cdc6b3909_total_assets_before_deposit)
     (< 0 cdc6b3909_later_deposit_amount)))
(define-fun report_safety () Bool (=> (and (< 0 cdc6b3909_later_deposit_amount)
         cdc6b3909_shares_computed_from_pre_deposit_snapshot)
    cdc6b3909_precomputed_shares_minted))
(define-fun report_effects () Bool (and (< 0 cdc6b3909_later_deposit_amount)
     cdc6b3909_shares_computed_from_pre_deposit_snapshot
     (not cdc6b3909_precomputed_shares_minted)
     (= 0 cdc6b3909_minted_shares_for_later_deposit)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
