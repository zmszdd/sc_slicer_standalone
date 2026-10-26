; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb2a43d46_accrued_launchpad_fees_nonzero () Bool)
(declare-fun cb2a43d46_amount0_out_equals_total_launchpad_fee0 () Bool)
(declare-fun cb2a43d46_attacker_transfers_no_tokens_before_swap () Bool)
(declare-fun cb2a43d46_fees_subtracted_before_k_check () Bool)
(declare-fun cb2a43d46_pair_tokens_stolen_up_to_100_percent () Bool)
(declare-fun cb2a43d46_reserves_equal_balances_minus_fees () Bool)
(assert
 (= cb2a43d46_accrued_launchpad_fees_nonzero cb2a43d46_accrued_launchpad_fees_nonzero))
(assert
 (= cb2a43d46_amount0_out_equals_total_launchpad_fee0 cb2a43d46_amount0_out_equals_total_launchpad_fee0))
(assert
 (= cb2a43d46_attacker_transfers_no_tokens_before_swap cb2a43d46_attacker_transfers_no_tokens_before_swap))
(assert
 (= cb2a43d46_fees_subtracted_before_k_check cb2a43d46_fees_subtracted_before_k_check))
(assert
 (= cb2a43d46_pair_tokens_stolen_up_to_100_percent cb2a43d46_pair_tokens_stolen_up_to_100_percent))
(assert
 (= cb2a43d46_reserves_equal_balances_minus_fees cb2a43d46_reserves_equal_balances_minus_fees))
(define-fun report_preconditions () Bool (and cb2a43d46_accrued_launchpad_fees_nonzero
     cb2a43d46_reserves_equal_balances_minus_fees
     cb2a43d46_attacker_transfers_no_tokens_before_swap
     cb2a43d46_amount0_out_equals_total_launchpad_fee0))
(define-fun report_safety () Bool (=> cb2a43d46_accrued_launchpad_fees_nonzero
    cb2a43d46_fees_subtracted_before_k_check))
(define-fun report_effects () Bool (and cb2a43d46_pair_tokens_stolen_up_to_100_percent
     cb2a43d46_pair_tokens_stolen_up_to_100_percent))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
