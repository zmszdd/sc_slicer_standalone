; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9a3e2d97_caller_chosen_target () Bool)
(declare-fun c9a3e2d97_caller_entitled_to_assets () Bool)
(declare-fun c9a3e2d97_pooled_balance_drained () Bool)
(declare-fun c9a3e2d97_router_holds_balance () Bool)
(assert
 (= c9a3e2d97_caller_chosen_target c9a3e2d97_caller_chosen_target))
(assert
 (= c9a3e2d97_caller_entitled_to_assets c9a3e2d97_caller_entitled_to_assets))
(assert
 (= c9a3e2d97_pooled_balance_drained c9a3e2d97_pooled_balance_drained))
(assert
 (= c9a3e2d97_router_holds_balance c9a3e2d97_router_holds_balance))
(define-fun report_preconditions () Bool (and c9a3e2d97_router_holds_balance c9a3e2d97_caller_chosen_target))
(define-fun report_safety () Bool (=> (and c9a3e2d97_router_holds_balance
         c9a3e2d97_caller_chosen_target
         (not c9a3e2d97_caller_entitled_to_assets))
    (not c9a3e2d97_pooled_balance_drained)))
(define-fun report_effects () Bool (and c9a3e2d97_router_holds_balance
     c9a3e2d97_caller_chosen_target
     (not c9a3e2d97_caller_entitled_to_assets)
     (not (not c9a3e2d97_pooled_balance_drained))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
