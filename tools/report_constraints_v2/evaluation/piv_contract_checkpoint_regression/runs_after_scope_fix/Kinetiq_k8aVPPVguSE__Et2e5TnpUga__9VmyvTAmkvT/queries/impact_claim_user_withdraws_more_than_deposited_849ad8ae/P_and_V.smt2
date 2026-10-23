; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce9e3d56e_requeued_with_returned_khype () Bool)
(declare-fun ce9e3d56e_staked_eth_amount () Int)
(declare-fun ce9e3d56e_withdrawal_cancelled_before_processing () Bool)
(declare-fun ce9e3d56e_withdrawal_queued () Bool)
(declare-fun ce9e3d56e_withdrawn_eth_amount () Int)
(assert
 (= ce9e3d56e_requeued_with_returned_khype ce9e3d56e_requeued_with_returned_khype))
(assert
 (= ce9e3d56e_staked_eth_amount ce9e3d56e_staked_eth_amount))
(assert
 (= ce9e3d56e_withdrawal_cancelled_before_processing ce9e3d56e_withdrawal_cancelled_before_processing))
(assert
 (= ce9e3d56e_withdrawal_queued ce9e3d56e_withdrawal_queued))
(assert
 (= ce9e3d56e_withdrawn_eth_amount ce9e3d56e_withdrawn_eth_amount))
(define-fun report_preconditions () Bool (and (= 1 ce9e3d56e_staked_eth_amount)
     ce9e3d56e_withdrawal_queued
     ce9e3d56e_withdrawal_cancelled_before_processing
     ce9e3d56e_requeued_with_returned_khype))
(define-fun report_safety () Bool (=> (and (= 1 ce9e3d56e_staked_eth_amount)
         ce9e3d56e_withdrawal_queued
         ce9e3d56e_withdrawal_cancelled_before_processing
         ce9e3d56e_requeued_with_returned_khype)
    (<= ce9e3d56e_withdrawn_eth_amount ce9e3d56e_staked_eth_amount)))
(define-fun report_effects () Bool (and (= 1 ce9e3d56e_staked_eth_amount)
     ce9e3d56e_withdrawal_queued
     ce9e3d56e_withdrawal_cancelled_before_processing
     ce9e3d56e_requeued_with_returned_khype
     (not (<= ce9e3d56e_withdrawn_eth_amount ce9e3d56e_staked_eth_amount))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
