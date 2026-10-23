; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce689a5c9_caller_authorized_for_router_assets () Bool)
(declare-fun ce689a5c9_pooled_balances_drained () Bool)
(declare-fun ce689a5c9_router_holds_erc20 () Bool)
(declare-fun ce689a5c9_tokens_stranded_by_victims () Bool)
(assert
 (= ce689a5c9_caller_authorized_for_router_assets ce689a5c9_caller_authorized_for_router_assets))
(assert
 (= ce689a5c9_pooled_balances_drained ce689a5c9_pooled_balances_drained))
(assert
 (= ce689a5c9_router_holds_erc20 ce689a5c9_router_holds_erc20))
(assert
 (= ce689a5c9_tokens_stranded_by_victims ce689a5c9_tokens_stranded_by_victims))
(define-fun report_preconditions () Bool (and ce689a5c9_router_holds_erc20 ce689a5c9_tokens_stranded_by_victims))
(define-fun report_safety () Bool (=> (and ce689a5c9_router_holds_erc20
         ce689a5c9_tokens_stranded_by_victims
         (not ce689a5c9_caller_authorized_for_router_assets))
    (not ce689a5c9_pooled_balances_drained)))
(define-fun report_effects () Bool (and ce689a5c9_router_holds_erc20
     ce689a5c9_tokens_stranded_by_victims
     (not ce689a5c9_caller_authorized_for_router_assets)
     (not (not ce689a5c9_pooled_balances_drained))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
