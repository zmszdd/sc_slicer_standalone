; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c51957eef_caller_is_factory () Bool)
(declare-fun c51957eef_init_call_succeeds () Bool)
(declare-fun c51957eef_init_factory_restricted () Bool)
(declare-fun c51957eef_init_publicly_callable () Bool)
(declare-fun c51957eef_init_reinit_protected () Bool)
(declare-fun c51957eef_total_asset_loss_occurs () Bool)
(declare-fun c51957eef_wallet_deployed_by_factory () Bool)
(assert
 (= c51957eef_caller_is_factory c51957eef_caller_is_factory))
(assert
 (= c51957eef_init_call_succeeds c51957eef_init_call_succeeds))
(assert
 (= c51957eef_init_factory_restricted c51957eef_init_factory_restricted))
(assert
 (= c51957eef_init_publicly_callable c51957eef_init_publicly_callable))
(assert
 (= c51957eef_init_reinit_protected c51957eef_init_reinit_protected))
(assert
 (= c51957eef_total_asset_loss_occurs c51957eef_total_asset_loss_occurs))
(assert
 (= c51957eef_wallet_deployed_by_factory c51957eef_wallet_deployed_by_factory))
(define-fun report_preconditions () Bool (and c51957eef_wallet_deployed_by_factory
     c51957eef_init_publicly_callable
     (not c51957eef_init_factory_restricted)
     (not c51957eef_init_reinit_protected)))
(define-fun report_safety () Bool (=> c51957eef_init_call_succeeds c51957eef_caller_is_factory))
(define-fun report_effects () Bool (and c51957eef_init_call_succeeds
     (not c51957eef_caller_is_factory)
     c51957eef_total_asset_loss_occurs))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
