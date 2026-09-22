; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ve_token_id_nonzero () Bool)
(declare-fun prior_total_supply_positive () Bool)
(declare-fun deposit_amount_positive () Bool)
(declare-fun lock_before_calc () Bool)
(declare-fun shares_underminted () Bool)
(assert
 (= ve_token_id_nonzero ve_token_id_nonzero))
(assert
 (= prior_total_supply_positive prior_total_supply_positive))
(assert
 (= deposit_amount_positive deposit_amount_positive))
(assert
 (= lock_before_calc lock_before_calc))
(assert
 (= shares_underminted shares_underminted))
(define-fun report_preconditions () Bool (and ve_token_id_nonzero
     prior_total_supply_positive
     deposit_amount_positive
     lock_before_calc))
(define-fun report_safety () Bool (=> lock_before_calc (not shares_underminted)))
(define-fun report_effects () Bool (and lock_before_calc shares_underminted))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
