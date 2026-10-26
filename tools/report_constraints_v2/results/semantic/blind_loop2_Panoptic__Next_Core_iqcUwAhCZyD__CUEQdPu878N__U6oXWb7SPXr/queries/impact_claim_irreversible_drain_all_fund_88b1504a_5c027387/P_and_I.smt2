; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd59d353b_all_funds_drained () Bool)
(declare-fun cd59d353b_caller_is_builder_admin () Bool)
(declare-fun cd59d353b_init_factory_restricted () Bool)
(declare-fun cd59d353b_init_publicly_callable () Bool)
(declare-fun cd59d353b_init_reinit_protected () Bool)
(declare-fun cd59d353b_sweep_called () Bool)
(declare-fun cd59d353b_wallet_deployed_by_factory () Bool)
(assert
 (= cd59d353b_all_funds_drained cd59d353b_all_funds_drained))
(assert
 (= cd59d353b_caller_is_builder_admin cd59d353b_caller_is_builder_admin))
(assert
 (= cd59d353b_init_factory_restricted cd59d353b_init_factory_restricted))
(assert
 (= cd59d353b_init_publicly_callable cd59d353b_init_publicly_callable))
(assert
 (= cd59d353b_init_reinit_protected cd59d353b_init_reinit_protected))
(assert
 (= cd59d353b_sweep_called cd59d353b_sweep_called))
(assert
 (= cd59d353b_wallet_deployed_by_factory cd59d353b_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and cd59d353b_wallet_deployed_by_factory
     cd59d353b_init_publicly_callable
     (not cd59d353b_init_factory_restricted)
     (not cd59d353b_init_reinit_protected)))
(define-fun report_safety () Bool (=> cd59d353b_sweep_called cd59d353b_caller_is_builder_admin))
(define-fun report_effects () Bool (and cd59d353b_sweep_called
     (not cd59d353b_caller_is_builder_admin)
     cd59d353b_all_funds_drained
     cd59d353b_all_funds_drained))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
