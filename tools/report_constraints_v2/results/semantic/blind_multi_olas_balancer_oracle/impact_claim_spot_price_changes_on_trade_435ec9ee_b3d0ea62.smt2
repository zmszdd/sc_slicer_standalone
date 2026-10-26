; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce8cbf502_oracle_price_source_is_raw_vault_balances () Bool)
(declare-fun ce8cbf502_oracle_used_for_slippage_protection () Bool)
(declare-fun ce8cbf502_raw_vault_balances_used_as_oracle () Bool)
(declare-fun ce8cbf502_spot_price_changes_on_trade () Bool)
(assert
 (= ce8cbf502_oracle_price_source_is_raw_vault_balances ce8cbf502_oracle_price_source_is_raw_vault_balances))
(assert
 (= ce8cbf502_oracle_used_for_slippage_protection ce8cbf502_oracle_used_for_slippage_protection))
(assert
 (= ce8cbf502_raw_vault_balances_used_as_oracle ce8cbf502_raw_vault_balances_used_as_oracle))
(assert
 (= ce8cbf502_spot_price_changes_on_trade ce8cbf502_spot_price_changes_on_trade))
(define-fun report_preconditions () Bool ce8cbf502_oracle_price_source_is_raw_vault_balances)
(define-fun report_safety () Bool (=> ce8cbf502_oracle_used_for_slippage_protection
    (= ce8cbf502_raw_vault_balances_used_as_oracle
       ce8cbf502_oracle_price_source_is_raw_vault_balances)))
(define-fun report_effects () Bool (and ce8cbf502_spot_price_changes_on_trade
     ce8cbf502_spot_price_changes_on_trade))
