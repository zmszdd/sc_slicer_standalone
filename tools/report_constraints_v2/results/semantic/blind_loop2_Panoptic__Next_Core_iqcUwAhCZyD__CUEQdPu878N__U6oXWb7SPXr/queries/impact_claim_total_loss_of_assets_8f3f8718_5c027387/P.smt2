; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0fbe9cff_all_assets_drained () Bool)
(declare-fun c0fbe9cff_caller_is_builder_admin () Bool)
(declare-fun c0fbe9cff_init_factory_restricted () Bool)
(declare-fun c0fbe9cff_init_publicly_callable () Bool)
(declare-fun c0fbe9cff_init_reinit_protected () Bool)
(declare-fun c0fbe9cff_sweep_called () Bool)
(declare-fun c0fbe9cff_wallet_deployed_by_factory () Bool)
(assert
 (= c0fbe9cff_all_assets_drained c0fbe9cff_all_assets_drained))
(assert
 (= c0fbe9cff_caller_is_builder_admin c0fbe9cff_caller_is_builder_admin))
(assert
 (= c0fbe9cff_init_factory_restricted c0fbe9cff_init_factory_restricted))
(assert
 (= c0fbe9cff_init_publicly_callable c0fbe9cff_init_publicly_callable))
(assert
 (= c0fbe9cff_init_reinit_protected c0fbe9cff_init_reinit_protected))
(assert
 (= c0fbe9cff_sweep_called c0fbe9cff_sweep_called))
(assert
 (= c0fbe9cff_wallet_deployed_by_factory c0fbe9cff_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and c0fbe9cff_wallet_deployed_by_factory
     c0fbe9cff_init_publicly_callable
     (not c0fbe9cff_init_factory_restricted)
     (not c0fbe9cff_init_reinit_protected)))
(define-fun report_safety () Bool (=> c0fbe9cff_sweep_called c0fbe9cff_caller_is_builder_admin))
(define-fun report_effects () Bool (and c0fbe9cff_sweep_called
     (not c0fbe9cff_caller_is_builder_admin)
     c0fbe9cff_all_assets_drained))
(assert report_preconditions)
(check-sat)
(get-model)
