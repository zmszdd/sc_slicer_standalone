; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3b45308c_accountant_is_configured () Bool)
(declare-fun c3b45308c_accounting_reads_and_settlement_revert_occurred () Bool)
(declare-fun c3b45308c_active_registration_exists () Bool)
(declare-fun c3b45308c_hypercore_activation_asynchronous () Bool)
(declare-fun c3b45308c_registration_promoted_after_successful_read () Bool)
(assert
 (= c3b45308c_accountant_is_configured c3b45308c_accountant_is_configured))
(assert
 (= c3b45308c_accounting_reads_and_settlement_revert_occurred c3b45308c_accounting_reads_and_settlement_revert_occurred))
(assert
 (= c3b45308c_active_registration_exists c3b45308c_active_registration_exists))
(assert
 (= c3b45308c_hypercore_activation_asynchronous c3b45308c_hypercore_activation_asynchronous))
(assert
 (= c3b45308c_registration_promoted_after_successful_read c3b45308c_registration_promoted_after_successful_read))
(define-fun report_preconditions () Bool (and c3b45308c_accountant_is_configured
     (not c3b45308c_active_registration_exists)))
(define-fun report_safety () Bool (=> (and c3b45308c_hypercore_activation_asynchronous
         (not c3b45308c_active_registration_exists))
    c3b45308c_registration_promoted_after_successful_read))
(define-fun report_effects () Bool (and c3b45308c_accounting_reads_and_settlement_revert_occurred
     c3b45308c_accounting_reads_and_settlement_revert_occurred))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
