; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2bb84bde_command_one_still_queued_after_cancel () Bool)
(declare-fun c2bb84bde_eth_withdrawn_from_validator () Int)
(declare-fun c2bb84bde_staked_eth_amount () Int)
(declare-fun c2bb84bde_withdrawal_one_queued () Bool)
(declare-fun c2bb84bde_withdrawal_two_queued () Bool)
(assert
 (= c2bb84bde_command_one_still_queued_after_cancel c2bb84bde_command_one_still_queued_after_cancel))
(assert
 (= c2bb84bde_eth_withdrawn_from_validator c2bb84bde_eth_withdrawn_from_validator))
(assert
 (= c2bb84bde_staked_eth_amount c2bb84bde_staked_eth_amount))
(assert
 (= c2bb84bde_withdrawal_one_queued c2bb84bde_withdrawal_one_queued))
(assert
 (= c2bb84bde_withdrawal_two_queued c2bb84bde_withdrawal_two_queued))
(define-fun report_preconditions () Bool (and (= 1 c2bb84bde_staked_eth_amount)
     c2bb84bde_withdrawal_one_queued
     c2bb84bde_command_one_still_queued_after_cancel
     c2bb84bde_withdrawal_two_queued))
(define-fun report_safety () Bool (=> (and (= 1 c2bb84bde_staked_eth_amount)
         c2bb84bde_withdrawal_one_queued
         c2bb84bde_command_one_still_queued_after_cancel
         c2bb84bde_withdrawal_two_queued)
    (<= c2bb84bde_eth_withdrawn_from_validator c2bb84bde_staked_eth_amount)))
(define-fun report_effects () Bool (and (= 1 c2bb84bde_staked_eth_amount)
     c2bb84bde_withdrawal_one_queued
     c2bb84bde_command_one_still_queued_after_cancel
     c2bb84bde_withdrawal_two_queued
     (not (<= c2bb84bde_eth_withdrawn_from_validator
              c2bb84bde_staked_eth_amount))))
