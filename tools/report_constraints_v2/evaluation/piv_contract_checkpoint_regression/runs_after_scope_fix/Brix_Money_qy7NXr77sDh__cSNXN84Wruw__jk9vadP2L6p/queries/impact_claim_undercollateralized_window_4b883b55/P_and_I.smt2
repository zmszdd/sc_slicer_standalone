; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4ba09faa_other_redemptions_fail () Bool)
(declare-fun c4ba09faa_rebalance_callable_by_any_caller () Bool)
(declare-fun c4ba09faa_rebalance_called_after_redemption () Bool)
(declare-fun c4ba09faa_vault_balance_reduced_by_redemption () Bool)
(declare-fun c4ba09faa_vault_temporarily_undercollateralized () Bool)
(assert
 (= c4ba09faa_other_redemptions_fail c4ba09faa_other_redemptions_fail))
(assert
 (= c4ba09faa_rebalance_callable_by_any_caller c4ba09faa_rebalance_callable_by_any_caller))
(assert
 (= c4ba09faa_rebalance_called_after_redemption c4ba09faa_rebalance_called_after_redemption))
(assert
 (= c4ba09faa_vault_balance_reduced_by_redemption c4ba09faa_vault_balance_reduced_by_redemption))
(assert
 (= c4ba09faa_vault_temporarily_undercollateralized c4ba09faa_vault_temporarily_undercollateralized))
(define-fun report_preconditions () Bool (and c4ba09faa_rebalance_callable_by_any_caller
     c4ba09faa_vault_balance_reduced_by_redemption))
(define-fun report_safety () Bool (=> (and c4ba09faa_rebalance_called_after_redemption
         c4ba09faa_vault_temporarily_undercollateralized)
    (not c4ba09faa_other_redemptions_fail)))
(define-fun report_effects () Bool (and c4ba09faa_rebalance_called_after_redemption
     c4ba09faa_vault_temporarily_undercollateralized
     (not (not c4ba09faa_other_redemptions_fail))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
