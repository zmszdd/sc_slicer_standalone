; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c554556_caller_authorized_for_assets () Bool)
(declare-fun c9c554556_router_holds_erc20 () Bool)
(declare-fun c9c554556_stranded_tokens_forwarded_out () Bool)
(declare-fun c9c554556_tokens_stranded_by_victims () Bool)
(assert
 (= c9c554556_caller_authorized_for_assets c9c554556_caller_authorized_for_assets))
(assert
 (= c9c554556_router_holds_erc20 c9c554556_router_holds_erc20))
(assert
 (= c9c554556_stranded_tokens_forwarded_out c9c554556_stranded_tokens_forwarded_out))
(assert
 (= c9c554556_tokens_stranded_by_victims c9c554556_tokens_stranded_by_victims))
(define-fun report_preconditions () Bool (and c9c554556_router_holds_erc20 c9c554556_tokens_stranded_by_victims))
(define-fun report_safety () Bool (=> (and c9c554556_router_holds_erc20 c9c554556_tokens_stranded_by_victims)
    (or c9c554556_caller_authorized_for_assets
        (not c9c554556_stranded_tokens_forwarded_out))))
(define-fun report_effects () Bool (and c9c554556_router_holds_erc20
     c9c554556_tokens_stranded_by_victims
     (not (or c9c554556_caller_authorized_for_assets
              (not c9c554556_stranded_tokens_forwarded_out)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
