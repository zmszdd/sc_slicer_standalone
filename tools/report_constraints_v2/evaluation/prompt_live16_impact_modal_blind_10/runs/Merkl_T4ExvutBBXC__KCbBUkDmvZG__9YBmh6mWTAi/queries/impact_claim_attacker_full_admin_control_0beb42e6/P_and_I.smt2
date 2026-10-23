; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2bfb8432_attacker_has_full_admin () Bool)
(declare-fun c2bfb8432_implementation_constructor_initialized_proxy () Bool)
(declare-fun c2bfb8432_initialize_caller_authorized () Bool)
(declare-fun c2bfb8432_proxy_initialized_flag () Int)
(assert
 (= c2bfb8432_attacker_has_full_admin c2bfb8432_attacker_has_full_admin))
(assert
 (= c2bfb8432_implementation_constructor_initialized_proxy c2bfb8432_implementation_constructor_initialized_proxy))
(assert
 (= c2bfb8432_initialize_caller_authorized c2bfb8432_initialize_caller_authorized))
(assert
 (= c2bfb8432_proxy_initialized_flag c2bfb8432_proxy_initialized_flag))
(define-fun report_preconditions () Bool (and (= 0 c2bfb8432_proxy_initialized_flag)
     (not c2bfb8432_initialize_caller_authorized)
     (not c2bfb8432_implementation_constructor_initialized_proxy)))
(define-fun report_safety () Bool (=> (and (= 0 c2bfb8432_proxy_initialized_flag)
         (not c2bfb8432_implementation_constructor_initialized_proxy))
    (or c2bfb8432_initialize_caller_authorized
        (not c2bfb8432_attacker_has_full_admin))))
(define-fun report_effects () Bool (and (= 0 c2bfb8432_proxy_initialized_flag)
     (not c2bfb8432_implementation_constructor_initialized_proxy)
     (not (or c2bfb8432_initialize_caller_authorized
              (not c2bfb8432_attacker_has_full_admin)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
