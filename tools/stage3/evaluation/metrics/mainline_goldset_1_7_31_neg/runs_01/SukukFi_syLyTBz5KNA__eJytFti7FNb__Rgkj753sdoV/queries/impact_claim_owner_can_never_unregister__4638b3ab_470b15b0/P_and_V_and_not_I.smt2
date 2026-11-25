; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ceb9f4741_owner_can_never_unregister_vault () Bool)
(declare-fun ceb9f4741_owner_can_recover_donated_assets () Bool)
(declare-fun ceb9f4741_vault_registered () Bool)
(assert
 (= ceb9f4741_owner_can_never_unregister_vault ceb9f4741_owner_can_never_unregister_vault))
(assert
 (= ceb9f4741_owner_can_recover_donated_assets ceb9f4741_owner_can_recover_donated_assets))
(assert
 (= ceb9f4741_vault_registered ceb9f4741_vault_registered))
(define-fun report_preconditions () Bool ceb9f4741_vault_registered)
(define-fun report_safety () Bool (=> ceb9f4741_vault_registered ceb9f4741_owner_can_recover_donated_assets))
(define-fun report_effects () Bool (and ceb9f4741_vault_registered
     (not ceb9f4741_owner_can_recover_donated_assets)
     ceb9f4741_owner_can_never_unregister_vault))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
