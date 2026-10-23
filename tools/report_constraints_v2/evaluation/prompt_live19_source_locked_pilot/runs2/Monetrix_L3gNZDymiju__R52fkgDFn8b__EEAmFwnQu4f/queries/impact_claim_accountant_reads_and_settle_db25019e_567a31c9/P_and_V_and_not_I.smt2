; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cce8d89a2_accountant_is_configured () Bool)
(declare-fun cce8d89a2_accountant_reads_and_settlement_revert_occurred () Bool)
(declare-fun cce8d89a2_active_registration_exists () Bool)
(declare-fun cce8d89a2_registration_promoted_after_successful_read () Bool)
(assert
 (= cce8d89a2_accountant_is_configured cce8d89a2_accountant_is_configured))
(assert
 (= cce8d89a2_accountant_reads_and_settlement_revert_occurred cce8d89a2_accountant_reads_and_settlement_revert_occurred))
(assert
 (= cce8d89a2_active_registration_exists cce8d89a2_active_registration_exists))
(assert
 (= cce8d89a2_registration_promoted_after_successful_read cce8d89a2_registration_promoted_after_successful_read))
(define-fun report_preconditions () Bool (and cce8d89a2_accountant_is_configured
     (not cce8d89a2_active_registration_exists)))
(define-fun report_safety () Bool (=> cce8d89a2_accountant_reads_and_settlement_revert_occurred
    (=> cce8d89a2_accountant_is_configured
        (= cce8d89a2_registration_promoted_after_successful_read
           cce8d89a2_registration_promoted_after_successful_read))))
(define-fun report_effects () Bool (and cce8d89a2_accountant_reads_and_settlement_revert_occurred
     cce8d89a2_accountant_is_configured
     (not (= cce8d89a2_registration_promoted_after_successful_read
             cce8d89a2_registration_promoted_after_successful_read))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
