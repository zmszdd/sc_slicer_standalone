; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb4f38ec0_attacker_gained_withdrawal_rights () Bool)
(declare-fun cb4f38ec0_caller_is_builder_admin () Bool)
(declare-fun cb4f38ec0_init_not_factory_restricted () Bool)
(declare-fun cb4f38ec0_init_not_reinit_protected () Bool)
(declare-fun cb4f38ec0_init_publicly_callable () Bool)
(declare-fun cb4f38ec0_sweep_called () Bool)
(declare-fun cb4f38ec0_wallet_deployed_by_factory () Bool)
(assert
 (= cb4f38ec0_attacker_gained_withdrawal_rights cb4f38ec0_attacker_gained_withdrawal_rights))
(assert
 (= cb4f38ec0_caller_is_builder_admin cb4f38ec0_caller_is_builder_admin))
(assert
 (= cb4f38ec0_init_not_factory_restricted cb4f38ec0_init_not_factory_restricted))
(assert
 (= cb4f38ec0_init_not_reinit_protected cb4f38ec0_init_not_reinit_protected))
(assert
 (= cb4f38ec0_init_publicly_callable cb4f38ec0_init_publicly_callable))
(assert
 (= cb4f38ec0_sweep_called cb4f38ec0_sweep_called))
(assert
 (= cb4f38ec0_wallet_deployed_by_factory cb4f38ec0_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and cb4f38ec0_wallet_deployed_by_factory
     cb4f38ec0_init_publicly_callable
     cb4f38ec0_init_not_factory_restricted
     cb4f38ec0_init_not_reinit_protected))
(define-fun report_safety () Bool (=> cb4f38ec0_sweep_called cb4f38ec0_caller_is_builder_admin))
(define-fun report_effects () Bool (and cb4f38ec0_sweep_called
     (not cb4f38ec0_caller_is_builder_admin)
     cb4f38ec0_attacker_gained_withdrawal_rights))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
