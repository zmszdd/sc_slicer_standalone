; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5999fd6a_attacker_gains_admin_and_drains () Bool)
(declare-fun c5999fd6a_caller_is_factory () Bool)
(declare-fun c5999fd6a_init_called () Bool)
(declare-fun c5999fd6a_init_restricted_to_factory () Bool)
(declare-fun c5999fd6a_reinit_protected () Bool)
(declare-fun c5999fd6a_wallet_deployed_by_factory () Bool)
(assert
 (= c5999fd6a_attacker_gains_admin_and_drains c5999fd6a_attacker_gains_admin_and_drains))
(assert
 (= c5999fd6a_caller_is_factory c5999fd6a_caller_is_factory))
(assert
 (= c5999fd6a_init_called c5999fd6a_init_called))
(assert
 (= c5999fd6a_init_restricted_to_factory c5999fd6a_init_restricted_to_factory))
(assert
 (= c5999fd6a_reinit_protected c5999fd6a_reinit_protected))
(assert
 (= c5999fd6a_wallet_deployed_by_factory c5999fd6a_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and c5999fd6a_wallet_deployed_by_factory
     c5999fd6a_init_called
     (not c5999fd6a_init_restricted_to_factory)
     (not c5999fd6a_reinit_protected)))
(define-fun report_safety () Bool (=> c5999fd6a_init_called c5999fd6a_caller_is_factory))
(define-fun report_effects () Bool (and c5999fd6a_attacker_gains_admin_and_drains
     (not c5999fd6a_caller_is_factory)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
