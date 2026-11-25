; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4ec0b898_no_outstanding_shares () Bool)
(declare-fun c4ec0b898_permanent_dos_governance () Bool)
(declare-fun c4ec0b898_unregister_completes () Bool)
(declare-fun c4ec0b898_vault_registered () Bool)
(assert
 (= c4ec0b898_no_outstanding_shares c4ec0b898_no_outstanding_shares))
(assert
 (= c4ec0b898_permanent_dos_governance c4ec0b898_permanent_dos_governance))
(assert
 (= c4ec0b898_unregister_completes c4ec0b898_unregister_completes))
(assert
 (= c4ec0b898_vault_registered c4ec0b898_vault_registered))
(define-fun report_preconditions () Bool (and c4ec0b898_vault_registered c4ec0b898_no_outstanding_shares))
(define-fun report_safety () Bool c4ec0b898_unregister_completes)
(define-fun report_effects () Bool (and c4ec0b898_no_outstanding_shares
     (not c4ec0b898_unregister_completes)
     c4ec0b898_permanent_dos_governance
     c4ec0b898_permanent_dos_governance))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
