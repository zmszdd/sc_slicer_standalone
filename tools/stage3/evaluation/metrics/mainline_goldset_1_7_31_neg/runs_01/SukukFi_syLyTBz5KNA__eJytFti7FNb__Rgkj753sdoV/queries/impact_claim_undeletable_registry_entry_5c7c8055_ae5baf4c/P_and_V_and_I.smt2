; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb010e9ca_outstanding_shares_exist () Bool)
(declare-fun cb010e9ca_registry_entry_permanent () Bool)
(declare-fun cb010e9ca_unregister_verifies_outstanding_shares () Bool)
(declare-fun cb010e9ca_vault_registered () Bool)
(assert
 (= cb010e9ca_outstanding_shares_exist cb010e9ca_outstanding_shares_exist))
(assert
 (= cb010e9ca_registry_entry_permanent cb010e9ca_registry_entry_permanent))
(assert
 (= cb010e9ca_unregister_verifies_outstanding_shares cb010e9ca_unregister_verifies_outstanding_shares))
(assert
 (= cb010e9ca_vault_registered cb010e9ca_vault_registered))
(define-fun report_preconditions () Bool cb010e9ca_vault_registered)
(define-fun report_safety () Bool (=> cb010e9ca_vault_registered
    (= cb010e9ca_unregister_verifies_outstanding_shares
       cb010e9ca_outstanding_shares_exist)))
(define-fun report_effects () Bool (and cb010e9ca_vault_registered
     (not (= cb010e9ca_unregister_verifies_outstanding_shares
             cb010e9ca_outstanding_shares_exist))
     cb010e9ca_registry_entry_permanent
     cb010e9ca_registry_entry_permanent))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
