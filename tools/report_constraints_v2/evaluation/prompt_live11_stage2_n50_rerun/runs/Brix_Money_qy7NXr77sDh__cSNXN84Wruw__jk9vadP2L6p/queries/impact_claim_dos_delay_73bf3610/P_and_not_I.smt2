; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c913b7d7e_caller_is_authorized () Bool)
(declare-fun c913b7d7e_rebalance_delayed_or_blocked () Bool)
(assert
 (= c913b7d7e_caller_is_authorized c913b7d7e_caller_is_authorized))
(assert
 (= c913b7d7e_rebalance_delayed_or_blocked c913b7d7e_rebalance_delayed_or_blocked))
(define-fun report_preconditions () Bool (not c913b7d7e_caller_is_authorized))
(define-fun report_safety () Bool (=> (not c913b7d7e_caller_is_authorized)
    (not c913b7d7e_rebalance_delayed_or_blocked)))
(define-fun report_effects () Bool (and (not c913b7d7e_caller_is_authorized)
     (not (not c913b7d7e_rebalance_delayed_or_blocked))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
