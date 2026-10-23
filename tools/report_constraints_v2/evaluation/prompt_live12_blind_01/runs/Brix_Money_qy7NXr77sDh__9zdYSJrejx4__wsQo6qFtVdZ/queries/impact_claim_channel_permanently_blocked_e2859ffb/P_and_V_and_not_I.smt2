; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c1110bf_channel_permanently_blocked_observed () Bool)
(declare-fun c4c1110bf_cross_chain_mint_message_arrived () Bool)
(declare-fun c4c1110bf_recipient_is_blacklisted () Bool)
(assert
 (= c4c1110bf_channel_permanently_blocked_observed c4c1110bf_channel_permanently_blocked_observed))
(assert
 (= c4c1110bf_cross_chain_mint_message_arrived c4c1110bf_cross_chain_mint_message_arrived))
(assert
 (= c4c1110bf_recipient_is_blacklisted c4c1110bf_recipient_is_blacklisted))
(define-fun report_preconditions () Bool (and c4c1110bf_recipient_is_blacklisted
     c4c1110bf_cross_chain_mint_message_arrived))
(define-fun report_safety () Bool (=> (and c4c1110bf_cross_chain_mint_message_arrived
         c4c1110bf_recipient_is_blacklisted)
    (not c4c1110bf_channel_permanently_blocked_observed)))
(define-fun report_effects () Bool (and c4c1110bf_cross_chain_mint_message_arrived
     c4c1110bf_recipient_is_blacklisted
     (not (not c4c1110bf_channel_permanently_blocked_observed))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
