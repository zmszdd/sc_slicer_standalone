; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0f665975_accrued_launchpad_fees_nonzero () Bool)
(declare-fun c0f665975_amount0_out_equals_total_launchpad_fee0 () Bool)
(declare-fun c0f665975_amount_in_inferred_excludes_fees () Bool)
(declare-fun c0f665975_attacker_transfers_no_tokens_before_swap () Bool)
(declare-fun c0f665975_pair_tokens_stolen_up_to_100pct () Bool)
(declare-fun c0f665975_reserves_equal_balances_minus_fees () Bool)
(assert
 (= c0f665975_accrued_launchpad_fees_nonzero c0f665975_accrued_launchpad_fees_nonzero))
(assert
 (= c0f665975_amount0_out_equals_total_launchpad_fee0 c0f665975_amount0_out_equals_total_launchpad_fee0))
(assert
 (= c0f665975_amount_in_inferred_excludes_fees c0f665975_amount_in_inferred_excludes_fees))
(assert
 (= c0f665975_attacker_transfers_no_tokens_before_swap c0f665975_attacker_transfers_no_tokens_before_swap))
(assert
 (= c0f665975_pair_tokens_stolen_up_to_100pct c0f665975_pair_tokens_stolen_up_to_100pct))
(assert
 (= c0f665975_reserves_equal_balances_minus_fees c0f665975_reserves_equal_balances_minus_fees))
(define-fun report_preconditions () Bool (and c0f665975_accrued_launchpad_fees_nonzero
     c0f665975_reserves_equal_balances_minus_fees
     c0f665975_attacker_transfers_no_tokens_before_swap
     c0f665975_amount0_out_equals_total_launchpad_fee0))
(define-fun report_safety () Bool (=> c0f665975_accrued_launchpad_fees_nonzero
    c0f665975_amount_in_inferred_excludes_fees))
(define-fun report_effects () Bool (and c0f665975_pair_tokens_stolen_up_to_100pct
     c0f665975_pair_tokens_stolen_up_to_100pct))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
