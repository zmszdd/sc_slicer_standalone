; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce9496389_assets_drained () Bool)
(declare-fun ce9496389_init_callable_by_any_address () Bool)
(declare-fun ce9496389_init_reinit_protected () Bool)
(declare-fun ce9496389_init_reinvoked () Bool)
(declare-fun ce9496389_init_restricted_to_factory () Bool)
(declare-fun ce9496389_wallet_deployed_by_factory () Bool)
(assert
 (= ce9496389_assets_drained ce9496389_assets_drained))
(assert
 (= ce9496389_init_callable_by_any_address ce9496389_init_callable_by_any_address))
(assert
 (= ce9496389_init_reinit_protected ce9496389_init_reinit_protected))
(assert
 (= ce9496389_init_reinvoked ce9496389_init_reinvoked))
(assert
 (= ce9496389_init_restricted_to_factory ce9496389_init_restricted_to_factory))
(assert
 (= ce9496389_wallet_deployed_by_factory ce9496389_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and ce9496389_wallet_deployed_by_factory
     ce9496389_init_callable_by_any_address
     (not ce9496389_init_restricted_to_factory)
     (not ce9496389_init_reinit_protected)))
(define-fun report_safety () Bool (=> ce9496389_init_reinvoked ce9496389_init_reinit_protected))
(define-fun report_effects () Bool (and ce9496389_init_reinvoked
     (not ce9496389_init_reinit_protected)
     ce9496389_assets_drained))
