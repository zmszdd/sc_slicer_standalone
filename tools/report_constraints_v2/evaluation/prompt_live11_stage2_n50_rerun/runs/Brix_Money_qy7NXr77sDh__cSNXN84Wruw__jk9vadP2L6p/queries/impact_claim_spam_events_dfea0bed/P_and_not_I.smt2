; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccb76e1ed_callback_token_in_use () Bool)
(declare-fun ccb76e1ed_caller_is_authorized () Bool)
(declare-fun ccb76e1ed_custodian_is_contract () Bool)
(declare-fun ccb76e1ed_rebalance_invoked () Bool)
(declare-fun ccb76e1ed_spam_events_emitted () Bool)
(assert
 (= ccb76e1ed_callback_token_in_use ccb76e1ed_callback_token_in_use))
(assert
 (= ccb76e1ed_caller_is_authorized ccb76e1ed_caller_is_authorized))
(assert
 (= ccb76e1ed_custodian_is_contract ccb76e1ed_custodian_is_contract))
(assert
 (= ccb76e1ed_rebalance_invoked ccb76e1ed_rebalance_invoked))
(assert
 (= ccb76e1ed_spam_events_emitted ccb76e1ed_spam_events_emitted))
(define-fun report_preconditions () Bool (and (not ccb76e1ed_caller_is_authorized)
     ccb76e1ed_custodian_is_contract
     ccb76e1ed_callback_token_in_use))
(define-fun report_safety () Bool (=> (and ccb76e1ed_rebalance_invoked (not ccb76e1ed_caller_is_authorized))
    (not ccb76e1ed_spam_events_emitted)))
(define-fun report_effects () Bool (and ccb76e1ed_rebalance_invoked
     (not ccb76e1ed_caller_is_authorized)
     (not (not ccb76e1ed_spam_events_emitted))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
