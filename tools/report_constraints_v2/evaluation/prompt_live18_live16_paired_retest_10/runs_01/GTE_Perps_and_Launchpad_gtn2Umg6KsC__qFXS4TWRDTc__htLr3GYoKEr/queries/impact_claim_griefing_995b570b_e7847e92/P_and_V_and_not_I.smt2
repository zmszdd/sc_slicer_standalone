; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c90cecab9_accounting_increased_before_transfer_from () Bool)
(declare-fun c90cecab9_claim_rewards_reentered_during_transfer_from () Bool)
(declare-fun c90cecab9_token_can_execute_during_transfer_from () Bool)
(assert
 (= c90cecab9_accounting_increased_before_transfer_from c90cecab9_accounting_increased_before_transfer_from))
(assert
 (= c90cecab9_claim_rewards_reentered_during_transfer_from c90cecab9_claim_rewards_reentered_during_transfer_from))
(assert
 (= c90cecab9_token_can_execute_during_transfer_from c90cecab9_token_can_execute_during_transfer_from))
(define-fun report_preconditions () Bool c90cecab9_token_can_execute_during_transfer_from)
(define-fun report_safety () Bool (=> (and c90cecab9_accounting_increased_before_transfer_from
         c90cecab9_claim_rewards_reentered_during_transfer_from)
    (=> (and c90cecab9_token_can_execute_during_transfer_from
             c90cecab9_accounting_increased_before_transfer_from)
        (not c90cecab9_claim_rewards_reentered_during_transfer_from))))
(define-fun report_effects () Bool (and c90cecab9_accounting_increased_before_transfer_from
     c90cecab9_claim_rewards_reentered_during_transfer_from
     c90cecab9_token_can_execute_during_transfer_from
     c90cecab9_accounting_increased_before_transfer_from
     (not (not c90cecab9_claim_rewards_reentered_during_transfer_from))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
