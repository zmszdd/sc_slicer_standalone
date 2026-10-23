; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce689a5c9_caller_is_asset_owner () Bool)
(declare-fun ce689a5c9_inject_and_call_exposed () Bool)
(declare-fun ce689a5c9_pooled_balances_drained () Bool)
(declare-fun ce689a5c9_router_holds_pooled_balance () Bool)
(assert
 (= ce689a5c9_caller_is_asset_owner ce689a5c9_caller_is_asset_owner))
(assert
 (= ce689a5c9_inject_and_call_exposed ce689a5c9_inject_and_call_exposed))
(assert
 (= ce689a5c9_pooled_balances_drained ce689a5c9_pooled_balances_drained))
(assert
 (= ce689a5c9_router_holds_pooled_balance ce689a5c9_router_holds_pooled_balance))
(define-fun report_preconditions () Bool (and ce689a5c9_router_holds_pooled_balance ce689a5c9_inject_and_call_exposed))
(define-fun report_safety () Bool (=> (and ce689a5c9_router_holds_pooled_balance
         ce689a5c9_inject_and_call_exposed
         (not ce689a5c9_caller_is_asset_owner))
    (not ce689a5c9_pooled_balances_drained)))
(define-fun report_effects () Bool (and ce689a5c9_router_holds_pooled_balance
     ce689a5c9_inject_and_call_exposed
     (not ce689a5c9_caller_is_asset_owner)
     (not (not ce689a5c9_pooled_balances_drained))))
(assert report_preconditions)
(check-sat)
(get-model)
