; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0707f016_all_funds_drained () Bool)
(declare-fun c0707f016_init_callable_by_any_address () Bool)
(declare-fun c0707f016_init_reinit_protected () Bool)
(declare-fun c0707f016_init_reinvoked () Bool)
(declare-fun c0707f016_init_restricted_to_factory () Bool)
(declare-fun c0707f016_wallet_deployed_by_factory () Bool)
(assert
 (= c0707f016_all_funds_drained c0707f016_all_funds_drained))
(assert
 (= c0707f016_init_callable_by_any_address c0707f016_init_callable_by_any_address))
(assert
 (= c0707f016_init_reinit_protected c0707f016_init_reinit_protected))
(assert
 (= c0707f016_init_reinvoked c0707f016_init_reinvoked))
(assert
 (= c0707f016_init_restricted_to_factory c0707f016_init_restricted_to_factory))
(assert
 (= c0707f016_wallet_deployed_by_factory c0707f016_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and c0707f016_wallet_deployed_by_factory
     c0707f016_init_callable_by_any_address
     (not c0707f016_init_restricted_to_factory)
     (not c0707f016_init_reinit_protected)))
(define-fun report_safety () Bool (=> c0707f016_init_reinvoked c0707f016_init_reinit_protected))
(define-fun report_effects () Bool (and c0707f016_init_reinvoked
     (not c0707f016_init_reinit_protected)
     c0707f016_all_funds_drained
     c0707f016_all_funds_drained))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
