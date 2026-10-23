; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd5d14da8_cancelled_before_processing () Bool)
(declare-fun cd5d14da8_staked_hype () Int)
(declare-fun cd5d14da8_withdrawal_queued () Bool)
(declare-fun cd5d14da8_withdrawn_hype () Int)
(assert
 (= cd5d14da8_cancelled_before_processing cd5d14da8_cancelled_before_processing))
(assert
 (= cd5d14da8_staked_hype cd5d14da8_staked_hype))
(assert
 (= cd5d14da8_withdrawal_queued cd5d14da8_withdrawal_queued))
(assert
 (= cd5d14da8_withdrawn_hype cd5d14da8_withdrawn_hype))
(define-fun report_preconditions () Bool (and (= 1 cd5d14da8_staked_hype)
     cd5d14da8_withdrawal_queued
     cd5d14da8_cancelled_before_processing))
(define-fun report_safety () Bool (=> (and (= 1 cd5d14da8_staked_hype)
         cd5d14da8_withdrawal_queued
         cd5d14da8_cancelled_before_processing)
    (<= cd5d14da8_withdrawn_hype cd5d14da8_staked_hype)))
(define-fun report_effects () Bool (and (= 1 cd5d14da8_staked_hype)
     cd5d14da8_withdrawal_queued
     cd5d14da8_cancelled_before_processing
     (not (<= cd5d14da8_withdrawn_hype cd5d14da8_staked_hype))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
