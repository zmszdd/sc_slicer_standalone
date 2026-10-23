; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c80df1299_accountant_is_configured () Bool)
(declare-fun c80df1299_accounting_reads_and_settlement_revert_occurred () Bool)
(declare-fun c80df1299_active_registration_exists () Bool)
(declare-fun c80df1299_hypercore_activation_asynchronous () Bool)
(declare-fun c80df1299_registration_promoted_after_successful_read () Bool)
(assert
 (= c80df1299_accountant_is_configured c80df1299_accountant_is_configured))
(assert
 (= c80df1299_accounting_reads_and_settlement_revert_occurred c80df1299_accounting_reads_and_settlement_revert_occurred))
(assert
 (= c80df1299_active_registration_exists c80df1299_active_registration_exists))
(assert
 (= c80df1299_hypercore_activation_asynchronous c80df1299_hypercore_activation_asynchronous))
(assert
 (= c80df1299_registration_promoted_after_successful_read c80df1299_registration_promoted_after_successful_read))
(define-fun report_preconditions () Bool (and c80df1299_accountant_is_configured
     (not c80df1299_active_registration_exists)))
(define-fun report_safety () Bool (=> c80df1299_accounting_reads_and_settlement_revert_occurred
    (=> (and c80df1299_accountant_is_configured
             (not c80df1299_active_registration_exists)
             c80df1299_hypercore_activation_asynchronous)
        c80df1299_registration_promoted_after_successful_read)))
(define-fun report_effects () Bool (and c80df1299_accounting_reads_and_settlement_revert_occurred
     c80df1299_accountant_is_configured
     (not c80df1299_active_registration_exists)
     c80df1299_hypercore_activation_asynchronous
     (not c80df1299_registration_promoted_after_successful_read)))
