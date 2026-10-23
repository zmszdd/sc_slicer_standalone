; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c88edc669_direct_call_allowed () Bool)
(declare-fun c88edc669_executes_in_user_wallet_context () Bool)
(declare-fun c88edc669_router_holds_user_funds () Bool)
(declare-fun c88edc669_target_call_faulty () Bool)
(declare-fun c88edc669_user_funds_sent_to_router () Bool)
(assert
 (= c88edc669_direct_call_allowed c88edc669_direct_call_allowed))
(assert
 (= c88edc669_executes_in_user_wallet_context c88edc669_executes_in_user_wallet_context))
(assert
 (= c88edc669_router_holds_user_funds c88edc669_router_holds_user_funds))
(assert
 (= c88edc669_target_call_faulty c88edc669_target_call_faulty))
(assert
 (= c88edc669_user_funds_sent_to_router c88edc669_user_funds_sent_to_router))
(define-fun report_preconditions () Bool (and c88edc669_direct_call_allowed
     c88edc669_user_funds_sent_to_router
     c88edc669_target_call_faulty))
(define-fun report_safety () Bool (=> (and c88edc669_direct_call_allowed c88edc669_user_funds_sent_to_router)
    (or c88edc669_executes_in_user_wallet_context
        (not c88edc669_router_holds_user_funds))))
(define-fun report_effects () Bool (and c88edc669_direct_call_allowed
     c88edc669_user_funds_sent_to_router
     (not (or c88edc669_executes_in_user_wallet_context
              (not c88edc669_router_holds_user_funds)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
