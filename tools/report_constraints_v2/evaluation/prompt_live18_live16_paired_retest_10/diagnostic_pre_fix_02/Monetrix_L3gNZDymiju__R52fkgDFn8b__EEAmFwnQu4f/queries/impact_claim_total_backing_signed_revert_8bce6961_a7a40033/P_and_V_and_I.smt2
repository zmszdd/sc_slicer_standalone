; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc1596d7d_accountant_is_configured () Bool)
(declare-fun cc1596d7d_active_registration_exists () Bool)
(declare-fun cc1596d7d_registration_pending () Bool)
(declare-fun cc1596d7d_supplied_balance_read_succeeded () Bool)
(declare-fun cc1596d7d_total_backing_signed_reverts_occurred () Bool)
(assert
 (= cc1596d7d_accountant_is_configured cc1596d7d_accountant_is_configured))
(assert
 (= cc1596d7d_active_registration_exists cc1596d7d_active_registration_exists))
(assert
 (= cc1596d7d_registration_pending cc1596d7d_registration_pending))
(assert
 (= cc1596d7d_supplied_balance_read_succeeded cc1596d7d_supplied_balance_read_succeeded))
(assert
 (= cc1596d7d_total_backing_signed_reverts_occurred cc1596d7d_total_backing_signed_reverts_occurred))
(define-fun report_preconditions () Bool (and cc1596d7d_accountant_is_configured
     (not cc1596d7d_active_registration_exists)))
(define-fun report_safety () Bool (=> cc1596d7d_total_backing_signed_reverts_occurred
    (=> (and cc1596d7d_accountant_is_configured
             (not cc1596d7d_active_registration_exists)
             cc1596d7d_registration_pending)
        (and cc1596d7d_supplied_balance_read_succeeded
             (not cc1596d7d_total_backing_signed_reverts_occurred)))))
(define-fun report_effects () Bool (and cc1596d7d_total_backing_signed_reverts_occurred
     cc1596d7d_accountant_is_configured
     (not cc1596d7d_active_registration_exists)
     cc1596d7d_registration_pending
     (not (and cc1596d7d_supplied_balance_read_succeeded
               (not cc1596d7d_total_backing_signed_reverts_occurred)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
