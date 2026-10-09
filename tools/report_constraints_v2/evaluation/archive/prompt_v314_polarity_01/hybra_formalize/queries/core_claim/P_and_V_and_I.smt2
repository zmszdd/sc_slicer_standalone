; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ve_token_id_nonzero () Bool)
(declare-fun total_supply_prior () Int)
(declare-fun total_assets_prior () Int)
(declare-fun total_supply_prior_value () Int)
(declare-fun deposit_amount () Int)
(assert
 (= ve_token_id_nonzero ve_token_id_nonzero))
(assert
 (= total_supply_prior total_supply_prior))
(assert
 (= total_assets_prior total_assets_prior))
(assert
 (= total_supply_prior_value total_supply_prior_value))
(assert
 (= deposit_amount deposit_amount))
(define-fun report_preconditions () Bool (and ve_token_id_nonzero
     (< 0 total_supply_prior)
     (= 100 total_assets_prior)
     (= 100 total_supply_prior_value)
     (= 100 deposit_amount)))
(define-fun report_safety () Bool (=> (and ve_token_id_nonzero (< 0 total_supply_prior) (< 0 deposit_amount))
    (= deposit_amount deposit_amount)))
(define-fun report_effects () Bool (and ve_token_id_nonzero
     (< 0 total_supply_prior)
     (< 0 deposit_amount)
     (not (= deposit_amount deposit_amount))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
