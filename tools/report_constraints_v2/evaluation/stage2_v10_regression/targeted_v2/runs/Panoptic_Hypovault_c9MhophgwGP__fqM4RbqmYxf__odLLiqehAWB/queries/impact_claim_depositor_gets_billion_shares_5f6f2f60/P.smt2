; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb7c0aeae_first_deposit_assets () Int)
(declare-fun cb7c0aeae_preset_total_supply () Int)
(declare-fun cb7c0aeae_shares_minted_to_depositor () Int)
(declare-fun cb7c0aeae_sum_of_balances_before () Int)
(assert
 (= cb7c0aeae_first_deposit_assets cb7c0aeae_first_deposit_assets))
(assert
 (= cb7c0aeae_preset_total_supply cb7c0aeae_preset_total_supply))
(assert
 (= cb7c0aeae_shares_minted_to_depositor cb7c0aeae_shares_minted_to_depositor))
(assert
 (= cb7c0aeae_sum_of_balances_before cb7c0aeae_sum_of_balances_before))
(define-fun report_preconditions () Bool (and (= 1000000 cb7c0aeae_preset_total_supply)
     (= 0 cb7c0aeae_sum_of_balances_before)
     (= 1000 cb7c0aeae_first_deposit_assets)))
(define-fun report_safety () Bool (=> (and (= 1000000 cb7c0aeae_preset_total_supply)
         (= 0 cb7c0aeae_sum_of_balances_before)
         (= 1000 cb7c0aeae_first_deposit_assets))
    (distinct 1000000000 cb7c0aeae_shares_minted_to_depositor)))
(define-fun report_effects () Bool (and (= 1000000 cb7c0aeae_preset_total_supply)
     (= 0 cb7c0aeae_sum_of_balances_before)
     (= 1000 cb7c0aeae_first_deposit_assets)
     (not (distinct 1000000000 cb7c0aeae_shares_minted_to_depositor))))
(assert report_preconditions)
(check-sat)
(get-model)
