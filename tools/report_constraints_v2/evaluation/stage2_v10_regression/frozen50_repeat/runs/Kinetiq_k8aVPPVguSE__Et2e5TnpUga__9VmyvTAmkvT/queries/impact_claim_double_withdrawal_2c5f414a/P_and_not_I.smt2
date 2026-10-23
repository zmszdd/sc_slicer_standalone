; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cad7e42ed_staked_eth () Int)
(declare-fun cad7e42ed_withdrawal_cancelled () Bool)
(declare-fun cad7e42ed_withdrawal_queued () Bool)
(declare-fun cad7e42ed_withdrawn_eth () Int)
(assert
 (= cad7e42ed_staked_eth cad7e42ed_staked_eth))
(assert
 (= cad7e42ed_withdrawal_cancelled cad7e42ed_withdrawal_cancelled))
(assert
 (= cad7e42ed_withdrawal_queued cad7e42ed_withdrawal_queued))
(assert
 (= cad7e42ed_withdrawn_eth cad7e42ed_withdrawn_eth))
(define-fun report_preconditions () Bool (and (= 1 cad7e42ed_staked_eth)
     cad7e42ed_withdrawal_queued
     cad7e42ed_withdrawal_cancelled))
(define-fun report_safety () Bool (=> (and (= 1 cad7e42ed_staked_eth)
         cad7e42ed_withdrawal_queued
         cad7e42ed_withdrawal_cancelled)
    (<= cad7e42ed_withdrawn_eth cad7e42ed_staked_eth)))
(define-fun report_effects () Bool (and (= 1 cad7e42ed_staked_eth)
     cad7e42ed_withdrawal_queued
     cad7e42ed_withdrawal_cancelled
     (not (<= cad7e42ed_withdrawn_eth cad7e42ed_staked_eth))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
