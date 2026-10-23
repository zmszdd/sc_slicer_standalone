; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c04ca434a_flash_loan_obtained () Bool)
(declare-fun c04ca434a_slippage_check_passed () Bool)
(declare-fun c04ca434a_spot_price_manipulated () Bool)
(assert
 (= c04ca434a_flash_loan_obtained c04ca434a_flash_loan_obtained))
(assert
 (= c04ca434a_slippage_check_passed c04ca434a_slippage_check_passed))
(assert
 (= c04ca434a_spot_price_manipulated c04ca434a_spot_price_manipulated))
(define-fun report_preconditions () Bool (and c04ca434a_flash_loan_obtained c04ca434a_spot_price_manipulated))
(define-fun report_safety () Bool (=> (and c04ca434a_flash_loan_obtained c04ca434a_spot_price_manipulated)
    (not c04ca434a_slippage_check_passed)))
(define-fun report_effects () Bool (and c04ca434a_flash_loan_obtained
     c04ca434a_spot_price_manipulated
     (not (not c04ca434a_slippage_check_passed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
