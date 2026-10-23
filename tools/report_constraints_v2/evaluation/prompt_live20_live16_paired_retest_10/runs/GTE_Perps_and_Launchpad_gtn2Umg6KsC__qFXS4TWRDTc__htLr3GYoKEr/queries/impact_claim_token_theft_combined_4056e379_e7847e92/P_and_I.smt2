; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c39deaf1a_add_rewards_unguarded () Bool)
(declare-fun c39deaf1a_claim_rewards_unguarded () Bool)
(declare-fun c39deaf1a_pending_accounting_increased () Bool)
(declare-fun c39deaf1a_reentrant_entrypoint_invoked () Bool)
(declare-fun c39deaf1a_tokens_stolen () Bool)
(declare-fun c39deaf1a_transfer_from_completed () Bool)
(assert
 (= c39deaf1a_add_rewards_unguarded c39deaf1a_add_rewards_unguarded))
(assert
 (= c39deaf1a_claim_rewards_unguarded c39deaf1a_claim_rewards_unguarded))
(assert
 (= c39deaf1a_pending_accounting_increased c39deaf1a_pending_accounting_increased))
(assert
 (= c39deaf1a_reentrant_entrypoint_invoked c39deaf1a_reentrant_entrypoint_invoked))
(assert
 (= c39deaf1a_tokens_stolen c39deaf1a_tokens_stolen))
(assert
 (= c39deaf1a_transfer_from_completed c39deaf1a_transfer_from_completed))
(define-fun report_preconditions () Bool (and c39deaf1a_add_rewards_unguarded c39deaf1a_claim_rewards_unguarded))
(define-fun report_safety () Bool (=> (and c39deaf1a_pending_accounting_increased
         (not c39deaf1a_transfer_from_completed))
    (not c39deaf1a_reentrant_entrypoint_invoked)))
(define-fun report_effects () Bool c39deaf1a_tokens_stolen)
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
