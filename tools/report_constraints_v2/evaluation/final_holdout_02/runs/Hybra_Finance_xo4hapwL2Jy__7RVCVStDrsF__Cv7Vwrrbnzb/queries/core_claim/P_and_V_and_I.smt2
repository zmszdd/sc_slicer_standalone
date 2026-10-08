; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun vault_assets_before () Int)
(declare-fun deposit_amount () Int)
(declare-fun shares_minted () Int)
(declare-fun total_shares_after () Int)
(declare-fun not_first_depositor () Bool)
(assert
 (= vault_assets_before vault_assets_before))
(assert
 (= deposit_amount deposit_amount))
(assert
 (= shares_minted shares_minted))
(assert
 (= total_shares_after total_shares_after))
(assert
 (= not_first_depositor not_first_depositor))
(define-fun report_preconditions () Bool (and (= 10000 vault_assets_before) (= 5000 deposit_amount) not_first_depositor))
(define-fun report_safety () Bool (=> (and not_first_depositor
         (= 10000 vault_assets_before)
         (= 5000 deposit_amount))
    (>= (* shares_minted vault_assets_before)
        (* deposit_amount total_shares_after))))
(define-fun report_effects () Bool (and not_first_depositor
     (= 10000 vault_assets_before)
     (= 5000 deposit_amount)
     (not (>= (* shares_minted vault_assets_before)
              (* deposit_amount total_shares_after)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
