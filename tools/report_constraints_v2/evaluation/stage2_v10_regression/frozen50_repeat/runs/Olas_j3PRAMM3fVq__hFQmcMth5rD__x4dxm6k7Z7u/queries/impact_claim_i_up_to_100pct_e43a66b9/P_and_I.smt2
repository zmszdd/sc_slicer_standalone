; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c197b8b44_amount_out_minimum () Int)
(declare-fun c197b8b44_buyback_tx_publicly_visible () Bool)
(declare-fun c197b8b44_effective_slippage_protection_enforced () Bool)
(declare-fun c197b8b44_sandwich_extraction_occurred () Bool)
(declare-fun c197b8b44_sqrt_price_limit_x96 () Int)
(declare-fun c197b8b44_swap_value_extracted_pct () Int)
(assert
 (= c197b8b44_amount_out_minimum c197b8b44_amount_out_minimum))
(assert
 (= c197b8b44_buyback_tx_publicly_visible c197b8b44_buyback_tx_publicly_visible))
(assert
 (= c197b8b44_effective_slippage_protection_enforced c197b8b44_effective_slippage_protection_enforced))
(assert
 (= c197b8b44_sandwich_extraction_occurred c197b8b44_sandwich_extraction_occurred))
(assert
 (= c197b8b44_sqrt_price_limit_x96 c197b8b44_sqrt_price_limit_x96))
(assert
 (= c197b8b44_swap_value_extracted_pct c197b8b44_swap_value_extracted_pct))
(define-fun report_preconditions () Bool (and c197b8b44_buyback_tx_publicly_visible
     (= 1 c197b8b44_amount_out_minimum)
     (= 0 c197b8b44_sqrt_price_limit_x96)))
(define-fun report_safety () Bool (=> (and c197b8b44_buyback_tx_publicly_visible
         (= 1 c197b8b44_amount_out_minimum)
         (= 0 c197b8b44_sqrt_price_limit_x96))
    (and c197b8b44_effective_slippage_protection_enforced
         (or (not c197b8b44_sandwich_extraction_occurred)
             (> 100 c197b8b44_swap_value_extracted_pct)))))
(define-fun report_effects () Bool (let ((a!1 (not (and c197b8b44_effective_slippage_protection_enforced
                     (or (not c197b8b44_sandwich_extraction_occurred)
                         (> 100 c197b8b44_swap_value_extracted_pct))))))
  (and c197b8b44_buyback_tx_publicly_visible
       (= 1 c197b8b44_amount_out_minimum)
       (= 0 c197b8b44_sqrt_price_limit_x96)
       a!1)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
