; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun user_is_smart_wallet () Bool)
(declare-fun signature_by_owner () Bool)
(declare-fun recovered_is_owner () Bool)
(declare-fun intent_accepted () Bool)
(assert
 (= user_is_smart_wallet user_is_smart_wallet))
(assert
 (= signature_by_owner signature_by_owner))
(assert
 (= recovered_is_owner recovered_is_owner))
(assert
 (= intent_accepted intent_accepted))
(define-fun report_preconditions () Bool (and user_is_smart_wallet signature_by_owner recovered_is_owner))
(define-fun report_safety () Bool (=> (and user_is_smart_wallet signature_by_owner recovered_is_owner)
    intent_accepted))
(define-fun report_effects () Bool (and user_is_smart_wallet
     signature_by_owner
     recovered_is_owner
     (not intent_accepted)))
