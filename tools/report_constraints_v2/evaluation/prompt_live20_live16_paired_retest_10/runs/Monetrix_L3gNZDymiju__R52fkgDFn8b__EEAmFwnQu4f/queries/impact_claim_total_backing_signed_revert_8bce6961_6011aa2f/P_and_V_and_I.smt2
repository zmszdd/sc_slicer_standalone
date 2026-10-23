; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfe3e1362_accountant_is_configured () Bool)
(declare-fun cfe3e1362_active_registration_exists () Bool)
(declare-fun cfe3e1362_distributable_surplus_reverts_occurred () Bool)
(declare-fun cfe3e1362_hypercore_activation_asynchronous () Bool)
(declare-fun cfe3e1362_registration_promoted_after_successful_read () Bool)
(declare-fun cfe3e1362_settle_daily_pnl_reverts_occurred () Bool)
(declare-fun cfe3e1362_total_backing_signed_reverts_occurred () Bool)
(assert
 (= cfe3e1362_accountant_is_configured cfe3e1362_accountant_is_configured))
(assert
 (= cfe3e1362_active_registration_exists cfe3e1362_active_registration_exists))
(assert
 (= cfe3e1362_distributable_surplus_reverts_occurred cfe3e1362_distributable_surplus_reverts_occurred))
(assert
 (= cfe3e1362_hypercore_activation_asynchronous cfe3e1362_hypercore_activation_asynchronous))
(assert
 (= cfe3e1362_registration_promoted_after_successful_read cfe3e1362_registration_promoted_after_successful_read))
(assert
 (= cfe3e1362_settle_daily_pnl_reverts_occurred cfe3e1362_settle_daily_pnl_reverts_occurred))
(assert
 (= cfe3e1362_total_backing_signed_reverts_occurred cfe3e1362_total_backing_signed_reverts_occurred))
(define-fun report_preconditions () Bool (and cfe3e1362_accountant_is_configured
     (not cfe3e1362_active_registration_exists)))
(define-fun report_safety () Bool (=> cfe3e1362_hypercore_activation_asynchronous
    cfe3e1362_registration_promoted_after_successful_read))
(define-fun report_effects () Bool (and cfe3e1362_total_backing_signed_reverts_occurred
     cfe3e1362_distributable_surplus_reverts_occurred
     cfe3e1362_settle_daily_pnl_reverts_occurred
     cfe3e1362_total_backing_signed_reverts_occurred))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
