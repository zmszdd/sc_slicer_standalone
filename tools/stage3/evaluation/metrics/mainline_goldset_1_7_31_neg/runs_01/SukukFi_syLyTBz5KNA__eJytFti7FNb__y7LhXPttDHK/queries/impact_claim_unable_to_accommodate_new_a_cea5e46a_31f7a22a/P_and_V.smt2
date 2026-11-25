; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf9515fa0_asset_vault_pair_count () Int)
(declare-fun cf9515fa0_new_asset_accommodated () Bool)
(declare-fun cf9515fa0_new_asset_blocked () Bool)
(declare-fun cf9515fa0_one_vault_per_asset () Bool)
(declare-fun cf9515fa0_vault_registered_for_asset () Bool)
(assert
 (= cf9515fa0_asset_vault_pair_count cf9515fa0_asset_vault_pair_count))
(assert
 (= cf9515fa0_new_asset_accommodated cf9515fa0_new_asset_accommodated))
(assert
 (= cf9515fa0_new_asset_blocked cf9515fa0_new_asset_blocked))
(assert
 (= cf9515fa0_one_vault_per_asset cf9515fa0_one_vault_per_asset))
(assert
 (= cf9515fa0_vault_registered_for_asset cf9515fa0_vault_registered_for_asset))
(define-fun report_preconditions () Bool (and cf9515fa0_vault_registered_for_asset cf9515fa0_one_vault_per_asset))
(define-fun report_safety () Bool (=> (<= 10 cf9515fa0_asset_vault_pair_count) cf9515fa0_new_asset_accommodated))
(define-fun report_effects () Bool (and (<= 10 cf9515fa0_asset_vault_pair_count)
     (not cf9515fa0_new_asset_accommodated)
     cf9515fa0_new_asset_blocked
     (<= 10 cf9515fa0_asset_vault_pair_count)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
