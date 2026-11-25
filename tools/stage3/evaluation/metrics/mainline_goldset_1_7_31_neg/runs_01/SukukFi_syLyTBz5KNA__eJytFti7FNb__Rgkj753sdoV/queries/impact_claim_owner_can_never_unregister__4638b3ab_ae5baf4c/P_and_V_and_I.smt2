; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf91d9005_no_outstanding_shares () Bool)
(declare-fun cf91d9005_owner_cannot_unregister_vault () Bool)
(declare-fun cf91d9005_unregister_vault_succeeds () Bool)
(declare-fun cf91d9005_vault_registered () Bool)
(assert
 (= cf91d9005_no_outstanding_shares cf91d9005_no_outstanding_shares))
(assert
 (= cf91d9005_owner_cannot_unregister_vault cf91d9005_owner_cannot_unregister_vault))
(assert
 (= cf91d9005_unregister_vault_succeeds cf91d9005_unregister_vault_succeeds))
(assert
 (= cf91d9005_vault_registered cf91d9005_vault_registered))
(define-fun report_preconditions () Bool cf91d9005_vault_registered)
(define-fun report_safety () Bool (=> (and cf91d9005_vault_registered cf91d9005_no_outstanding_shares)
    cf91d9005_unregister_vault_succeeds))
(define-fun report_effects () Bool (and cf91d9005_vault_registered
     cf91d9005_no_outstanding_shares
     (not cf91d9005_unregister_vault_succeeds)
     cf91d9005_owner_cannot_unregister_vault))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
