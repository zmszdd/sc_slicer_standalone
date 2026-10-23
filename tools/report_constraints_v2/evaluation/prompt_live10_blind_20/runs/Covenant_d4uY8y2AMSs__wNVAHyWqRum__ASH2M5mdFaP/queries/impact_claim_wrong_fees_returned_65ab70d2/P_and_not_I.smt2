; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d0bb5a9_adapter_chain_configured () Bool)
(declare-fun c9d0bb5a9_correct_fee_expected () Int)
(declare-fun c9d0bb5a9_inverse_direction_call () Bool)
(declare-fun c9d0bb5a9_oracle_fee_returned () Int)
(assert
 (= c9d0bb5a9_adapter_chain_configured c9d0bb5a9_adapter_chain_configured))
(assert
 (= c9d0bb5a9_correct_fee_expected c9d0bb5a9_correct_fee_expected))
(assert
 (= c9d0bb5a9_inverse_direction_call c9d0bb5a9_inverse_direction_call))
(assert
 (= c9d0bb5a9_oracle_fee_returned c9d0bb5a9_oracle_fee_returned))
(define-fun report_preconditions () Bool (and c9d0bb5a9_inverse_direction_call c9d0bb5a9_adapter_chain_configured))
(define-fun report_safety () Bool (=> (and c9d0bb5a9_inverse_direction_call c9d0bb5a9_adapter_chain_configured)
    (= c9d0bb5a9_oracle_fee_returned c9d0bb5a9_correct_fee_expected)))
(define-fun report_effects () Bool (and c9d0bb5a9_inverse_direction_call
     c9d0bb5a9_adapter_chain_configured
     (not (= c9d0bb5a9_oracle_fee_returned c9d0bb5a9_correct_fee_expected))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
