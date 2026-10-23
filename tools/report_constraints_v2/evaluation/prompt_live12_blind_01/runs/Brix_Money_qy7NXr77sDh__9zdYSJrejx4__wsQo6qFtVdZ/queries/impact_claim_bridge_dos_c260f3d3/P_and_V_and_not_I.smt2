; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfd09ad64_bridge_blocked_for_other_users () Bool)
(declare-fun cfd09ad64_cross_chain_message_arrived () Bool)
(declare-fun cfd09ad64_recipient_is_blacklisted () Bool)
(assert
 (= cfd09ad64_bridge_blocked_for_other_users cfd09ad64_bridge_blocked_for_other_users))
(assert
 (= cfd09ad64_cross_chain_message_arrived cfd09ad64_cross_chain_message_arrived))
(assert
 (= cfd09ad64_recipient_is_blacklisted cfd09ad64_recipient_is_blacklisted))
(define-fun report_preconditions () Bool (and cfd09ad64_recipient_is_blacklisted cfd09ad64_cross_chain_message_arrived))
(define-fun report_safety () Bool (=> (and cfd09ad64_cross_chain_message_arrived
         cfd09ad64_recipient_is_blacklisted)
    (not cfd09ad64_bridge_blocked_for_other_users)))
(define-fun report_effects () Bool (and cfd09ad64_cross_chain_message_arrived
     cfd09ad64_recipient_is_blacklisted
     (not (not cfd09ad64_bridge_blocked_for_other_users))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
