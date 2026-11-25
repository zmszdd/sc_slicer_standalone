; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9c59fae5_no_outstanding_shares () Bool)
(declare-fun c9c59fae5_unregister_vault_blocked_permanently () Bool)
(declare-fun c9c59fae5_unregister_vault_completes () Bool)
(declare-fun c9c59fae5_vault_registered () Bool)
(assert
 (= c9c59fae5_no_outstanding_shares c9c59fae5_no_outstanding_shares))
(assert
 (= c9c59fae5_unregister_vault_blocked_permanently c9c59fae5_unregister_vault_blocked_permanently))
(assert
 (= c9c59fae5_unregister_vault_completes c9c59fae5_unregister_vault_completes))
(assert
 (= c9c59fae5_vault_registered c9c59fae5_vault_registered))
(define-fun report_preconditions () Bool (and c9c59fae5_vault_registered c9c59fae5_no_outstanding_shares))
(define-fun report_safety () Bool c9c59fae5_unregister_vault_completes)
(define-fun report_effects () Bool (and c9c59fae5_no_outstanding_shares
     (not c9c59fae5_unregister_vault_completes)
     c9c59fae5_unregister_vault_blocked_permanently
     c9c59fae5_unregister_vault_blocked_permanently))
