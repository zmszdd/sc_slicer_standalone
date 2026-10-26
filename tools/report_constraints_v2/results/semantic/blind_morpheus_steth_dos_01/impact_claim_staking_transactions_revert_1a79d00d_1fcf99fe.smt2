; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc47054a6_amount_passed_to_aave () Int)
(declare-fun cc47054a6_recipient_balance_increase () Int)
(declare-fun cc47054a6_staking_transaction_reverted () Bool)
(declare-fun cc47054a6_transfer_amount () Int)
(assert
 (= cc47054a6_amount_passed_to_aave cc47054a6_amount_passed_to_aave))
(assert
 (= cc47054a6_recipient_balance_increase cc47054a6_recipient_balance_increase))
(assert
 (= cc47054a6_staking_transaction_reverted cc47054a6_staking_transaction_reverted))
(assert
 (= cc47054a6_transfer_amount cc47054a6_transfer_amount))
(define-fun report_preconditions () Bool (= cc47054a6_recipient_balance_increase (- cc47054a6_transfer_amount 1)))
(define-fun report_safety () Bool (=> (not cc47054a6_staking_transaction_reverted)
    (= cc47054a6_amount_passed_to_aave cc47054a6_recipient_balance_increase)))
(define-fun report_effects () Bool cc47054a6_staking_transaction_reverted)
