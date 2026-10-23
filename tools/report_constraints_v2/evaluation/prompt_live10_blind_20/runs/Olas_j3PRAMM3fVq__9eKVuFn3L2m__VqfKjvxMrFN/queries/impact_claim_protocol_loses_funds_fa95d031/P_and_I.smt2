; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c582ac526_flash_loan_obtained () Bool)
(declare-fun c582ac526_pool_spot_price_manipulated () Bool)
(declare-fun c582ac526_protocol_funds_lost () Bool)
(declare-fun c582ac526_twap_distinct_from_spot () Bool)
(assert
 (= c582ac526_flash_loan_obtained c582ac526_flash_loan_obtained))
(assert
 (= c582ac526_pool_spot_price_manipulated c582ac526_pool_spot_price_manipulated))
(assert
 (= c582ac526_protocol_funds_lost c582ac526_protocol_funds_lost))
(assert
 (= c582ac526_twap_distinct_from_spot c582ac526_twap_distinct_from_spot))
(define-fun report_preconditions () Bool (and c582ac526_flash_loan_obtained c582ac526_pool_spot_price_manipulated))
(define-fun report_safety () Bool (=> (and c582ac526_flash_loan_obtained c582ac526_pool_spot_price_manipulated)
    (and c582ac526_twap_distinct_from_spot (not c582ac526_protocol_funds_lost))))
(define-fun report_effects () Bool (and c582ac526_flash_loan_obtained
     c582ac526_pool_spot_price_manipulated
     (not (and c582ac526_twap_distinct_from_spot
               (not c582ac526_protocol_funds_lost)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
