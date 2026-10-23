; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfc260822_any_address_can_call_rebalance () Bool)
(declare-fun cfc260822_caller_is_authorized () Bool)
(declare-fun cfc260822_rebalance_lacks_access_restriction () Bool)
(declare-fun cfc260822_unauthorized_rebalance_completed () Bool)
(assert
 (= cfc260822_any_address_can_call_rebalance cfc260822_any_address_can_call_rebalance))
(assert
 (= cfc260822_caller_is_authorized cfc260822_caller_is_authorized))
(assert
 (= cfc260822_rebalance_lacks_access_restriction cfc260822_rebalance_lacks_access_restriction))
(assert
 (= cfc260822_unauthorized_rebalance_completed cfc260822_unauthorized_rebalance_completed))
(define-fun report_preconditions () Bool (and cfc260822_rebalance_lacks_access_restriction
     cfc260822_any_address_can_call_rebalance))
(define-fun report_safety () Bool (=> (and cfc260822_rebalance_lacks_access_restriction
         cfc260822_any_address_can_call_rebalance
         (not cfc260822_caller_is_authorized))
    (not cfc260822_unauthorized_rebalance_completed)))
(define-fun report_effects () Bool (and cfc260822_rebalance_lacks_access_restriction
     cfc260822_any_address_can_call_rebalance
     (not cfc260822_caller_is_authorized)
     (not (not cfc260822_unauthorized_rebalance_completed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
