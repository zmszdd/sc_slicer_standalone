; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc3129026_command_1_queued () Bool)
(declare-fun cc3129026_command_1_remains_queued () Bool)
(declare-fun cc3129026_command_2_queued () Bool)
(declare-fun cc3129026_staked_eth () Int)
(declare-fun cc3129026_withdrawn_eth () Int)
(assert
 (= cc3129026_command_1_queued cc3129026_command_1_queued))
(assert
 (= cc3129026_command_1_remains_queued cc3129026_command_1_remains_queued))
(assert
 (= cc3129026_command_2_queued cc3129026_command_2_queued))
(assert
 (= cc3129026_staked_eth cc3129026_staked_eth))
(assert
 (= cc3129026_withdrawn_eth cc3129026_withdrawn_eth))
(define-fun report_preconditions () Bool (and (= 1 cc3129026_staked_eth)
     cc3129026_command_1_queued
     cc3129026_command_1_remains_queued
     cc3129026_command_2_queued))
(define-fun report_safety () Bool (=> (and cc3129026_command_1_queued
         cc3129026_command_1_remains_queued
         cc3129026_command_2_queued)
    (= cc3129026_withdrawn_eth cc3129026_staked_eth)))
(define-fun report_effects () Bool (and cc3129026_command_1_queued
     cc3129026_command_1_remains_queued
     cc3129026_command_2_queued
     (not (= cc3129026_withdrawn_eth cc3129026_staked_eth))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
