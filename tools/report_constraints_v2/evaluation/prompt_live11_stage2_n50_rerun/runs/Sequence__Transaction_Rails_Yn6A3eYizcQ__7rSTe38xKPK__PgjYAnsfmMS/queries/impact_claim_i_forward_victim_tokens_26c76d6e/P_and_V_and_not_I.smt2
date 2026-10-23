; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf4af38c4_caller_is_asset_owner () Bool)
(declare-fun cf4af38c4_inject_and_call_exposed () Bool)
(declare-fun cf4af38c4_router_holds_pooled_balance () Bool)
(declare-fun cf4af38c4_victim_tokens_forwarded_out () Bool)
(assert
 (= cf4af38c4_caller_is_asset_owner cf4af38c4_caller_is_asset_owner))
(assert
 (= cf4af38c4_inject_and_call_exposed cf4af38c4_inject_and_call_exposed))
(assert
 (= cf4af38c4_router_holds_pooled_balance cf4af38c4_router_holds_pooled_balance))
(assert
 (= cf4af38c4_victim_tokens_forwarded_out cf4af38c4_victim_tokens_forwarded_out))
(define-fun report_preconditions () Bool (and cf4af38c4_router_holds_pooled_balance cf4af38c4_inject_and_call_exposed))
(define-fun report_safety () Bool (=> (and cf4af38c4_router_holds_pooled_balance
         cf4af38c4_inject_and_call_exposed
         (not cf4af38c4_caller_is_asset_owner))
    (not cf4af38c4_victim_tokens_forwarded_out)))
(define-fun report_effects () Bool (and cf4af38c4_router_holds_pooled_balance
     cf4af38c4_inject_and_call_exposed
     (not cf4af38c4_caller_is_asset_owner)
     (not (not cf4af38c4_victim_tokens_forwarded_out))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
