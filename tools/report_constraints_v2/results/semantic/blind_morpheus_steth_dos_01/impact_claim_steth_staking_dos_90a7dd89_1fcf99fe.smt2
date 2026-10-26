; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8ecfe2a8_actual_received_amount () Int)
(declare-fun c8ecfe2a8_amount_passed_to_aave () Int)
(declare-fun c8ecfe2a8_steth_recipient_balance_increase () Int)
(declare-fun c8ecfe2a8_steth_staking_dos_occurred () Bool)
(declare-fun c8ecfe2a8_steth_transfer_amount () Int)
(declare-fun c8ecfe2a8_steth_transfer_discrepancy_wei () Int)
(assert
 (= c8ecfe2a8_actual_received_amount c8ecfe2a8_actual_received_amount))
(assert
 (= c8ecfe2a8_amount_passed_to_aave c8ecfe2a8_amount_passed_to_aave))
(assert
 (= c8ecfe2a8_steth_recipient_balance_increase c8ecfe2a8_steth_recipient_balance_increase))
(assert
 (= c8ecfe2a8_steth_staking_dos_occurred c8ecfe2a8_steth_staking_dos_occurred))
(assert
 (= c8ecfe2a8_steth_transfer_amount c8ecfe2a8_steth_transfer_amount))
(assert
 (= c8ecfe2a8_steth_transfer_discrepancy_wei c8ecfe2a8_steth_transfer_discrepancy_wei))
(define-fun report_preconditions () Bool (= (- c8ecfe2a8_steth_transfer_amount c8ecfe2a8_steth_transfer_discrepancy_wei)
   c8ecfe2a8_steth_recipient_balance_increase))
(define-fun report_safety () Bool (=> (not c8ecfe2a8_steth_staking_dos_occurred)
    (= c8ecfe2a8_amount_passed_to_aave c8ecfe2a8_actual_received_amount)))
(define-fun report_effects () Bool c8ecfe2a8_steth_staking_dos_occurred)
