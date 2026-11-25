; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0aabda75_external_systems_rely_on_gettob () Bool)
(declare-fun c0aabda75_gettob_returns_potentially_stale_price () Bool)
(declare-fun c0aabda75_gettob_returns_price_from_expired_order () Bool)
(assert
 (= c0aabda75_external_systems_rely_on_gettob c0aabda75_external_systems_rely_on_gettob))
(assert
 (= c0aabda75_gettob_returns_potentially_stale_price c0aabda75_gettob_returns_potentially_stale_price))
(assert
 (= c0aabda75_gettob_returns_price_from_expired_order c0aabda75_gettob_returns_price_from_expired_order))
(define-fun report_preconditions () Bool c0aabda75_external_systems_rely_on_gettob)
(define-fun report_safety () Bool (=> c0aabda75_external_systems_rely_on_gettob
    (not c0aabda75_gettob_returns_price_from_expired_order)))
(define-fun report_effects () Bool (and c0aabda75_external_systems_rely_on_gettob
     c0aabda75_gettob_returns_price_from_expired_order
     c0aabda75_gettob_returns_potentially_stale_price))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
