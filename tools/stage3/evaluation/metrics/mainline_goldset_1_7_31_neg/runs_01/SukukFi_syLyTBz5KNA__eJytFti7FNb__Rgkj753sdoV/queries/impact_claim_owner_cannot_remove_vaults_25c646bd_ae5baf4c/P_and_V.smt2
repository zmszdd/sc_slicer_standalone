; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4e256ca0_no_outstanding_shares () Bool)
(declare-fun c4e256ca0_owner_cannot_remove_vaults_observed () Bool)
(declare-fun c4e256ca0_unregister_vault_completes () Bool)
(declare-fun c4e256ca0_vault_registered () Bool)
(assert
 (= c4e256ca0_no_outstanding_shares c4e256ca0_no_outstanding_shares))
(assert
 (= c4e256ca0_owner_cannot_remove_vaults_observed c4e256ca0_owner_cannot_remove_vaults_observed))
(assert
 (= c4e256ca0_unregister_vault_completes c4e256ca0_unregister_vault_completes))
(assert
 (= c4e256ca0_vault_registered c4e256ca0_vault_registered))
(define-fun report_preconditions () Bool c4e256ca0_vault_registered)
(define-fun report_safety () Bool (=> (and c4e256ca0_vault_registered c4e256ca0_no_outstanding_shares)
    c4e256ca0_unregister_vault_completes))
(define-fun report_effects () Bool (and c4e256ca0_vault_registered
     c4e256ca0_no_outstanding_shares
     (not c4e256ca0_unregister_vault_completes)
     c4e256ca0_owner_cannot_remove_vaults_observed))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
