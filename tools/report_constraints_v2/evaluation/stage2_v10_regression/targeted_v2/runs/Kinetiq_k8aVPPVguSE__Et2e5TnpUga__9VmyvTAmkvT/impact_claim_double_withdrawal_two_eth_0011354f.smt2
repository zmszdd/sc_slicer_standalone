; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1e7419f1_cancelled_before_processing () Bool)
(declare-fun c1e7419f1_l1_undelegate_executed_after_cancel () Bool)
(declare-fun c1e7419f1_staked_eth () Int)
(declare-fun c1e7419f1_withdrawal_queued () Bool)
(declare-fun c1e7419f1_withdrawn_eth () Int)
(assert
 (= c1e7419f1_cancelled_before_processing c1e7419f1_cancelled_before_processing))
(assert
 (= c1e7419f1_l1_undelegate_executed_after_cancel c1e7419f1_l1_undelegate_executed_after_cancel))
(assert
 (= c1e7419f1_staked_eth c1e7419f1_staked_eth))
(assert
 (= c1e7419f1_withdrawal_queued c1e7419f1_withdrawal_queued))
(assert
 (= c1e7419f1_withdrawn_eth c1e7419f1_withdrawn_eth))
(define-fun report_preconditions () Bool (and (= 1 c1e7419f1_staked_eth)
     c1e7419f1_withdrawal_queued
     c1e7419f1_cancelled_before_processing))
(define-fun report_safety () Bool (=> (and (= 1 c1e7419f1_staked_eth)
         c1e7419f1_withdrawal_queued
         c1e7419f1_cancelled_before_processing)
    (and (not c1e7419f1_l1_undelegate_executed_after_cancel)
         (<= c1e7419f1_withdrawn_eth c1e7419f1_staked_eth))))
(define-fun report_effects () Bool (and (= 1 c1e7419f1_staked_eth)
     c1e7419f1_withdrawal_queued
     c1e7419f1_cancelled_before_processing
     (not (and (not c1e7419f1_l1_undelegate_executed_after_cancel)
               (<= c1e7419f1_withdrawn_eth c1e7419f1_staked_eth)))))
