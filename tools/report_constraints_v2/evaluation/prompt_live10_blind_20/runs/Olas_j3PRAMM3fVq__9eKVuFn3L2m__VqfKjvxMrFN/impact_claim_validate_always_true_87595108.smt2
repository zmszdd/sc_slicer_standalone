; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c11e56e15_flash_loan_obtained () Bool)
(declare-fun c11e56e15_pool_price_manipulated () Bool)
(declare-fun c11e56e15_twap_distinct_from_spot () Bool)
(declare-fun c11e56e15_validate_price_returns_true () Bool)
(assert
 (= c11e56e15_flash_loan_obtained c11e56e15_flash_loan_obtained))
(assert
 (= c11e56e15_pool_price_manipulated c11e56e15_pool_price_manipulated))
(assert
 (= c11e56e15_twap_distinct_from_spot c11e56e15_twap_distinct_from_spot))
(assert
 (= c11e56e15_validate_price_returns_true c11e56e15_validate_price_returns_true))
(define-fun report_preconditions () Bool (and c11e56e15_flash_loan_obtained c11e56e15_pool_price_manipulated))
(define-fun report_safety () Bool (=> (and c11e56e15_flash_loan_obtained c11e56e15_pool_price_manipulated)
    (and c11e56e15_twap_distinct_from_spot
         (not c11e56e15_validate_price_returns_true))))
(define-fun report_effects () Bool (and c11e56e15_flash_loan_obtained
     c11e56e15_pool_price_manipulated
     (not (and c11e56e15_twap_distinct_from_spot
               (not c11e56e15_validate_price_returns_true)))))
