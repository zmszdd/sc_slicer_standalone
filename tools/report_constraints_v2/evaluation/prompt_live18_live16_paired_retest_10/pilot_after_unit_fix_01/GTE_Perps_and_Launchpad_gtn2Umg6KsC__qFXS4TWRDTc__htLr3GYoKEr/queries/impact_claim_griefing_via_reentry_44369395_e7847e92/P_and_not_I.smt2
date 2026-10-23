; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c683fcadc_add_rewards_called_with_reentrant_token () Bool)
(declare-fun c683fcadc_claim_rewards_entered_during_window () Bool)
(declare-fun c683fcadc_griefing_occurs () Bool)
(declare-fun c683fcadc_reentrancy_guard_absent () Bool)
(assert
 (= c683fcadc_add_rewards_called_with_reentrant_token c683fcadc_add_rewards_called_with_reentrant_token))
(assert
 (= c683fcadc_claim_rewards_entered_during_window c683fcadc_claim_rewards_entered_during_window))
(assert
 (= c683fcadc_griefing_occurs c683fcadc_griefing_occurs))
(assert
 (= c683fcadc_reentrancy_guard_absent c683fcadc_reentrancy_guard_absent))
(define-fun report_preconditions () Bool (and c683fcadc_add_rewards_called_with_reentrant_token
     c683fcadc_reentrancy_guard_absent))
(define-fun report_safety () Bool (=> c683fcadc_griefing_occurs
    (=> (and c683fcadc_add_rewards_called_with_reentrant_token
             c683fcadc_reentrancy_guard_absent)
        (not c683fcadc_claim_rewards_entered_during_window))))
(define-fun report_effects () Bool (and c683fcadc_griefing_occurs
     c683fcadc_add_rewards_called_with_reentrant_token
     c683fcadc_reentrancy_guard_absent
     (not (not c683fcadc_claim_rewards_entered_during_window))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
