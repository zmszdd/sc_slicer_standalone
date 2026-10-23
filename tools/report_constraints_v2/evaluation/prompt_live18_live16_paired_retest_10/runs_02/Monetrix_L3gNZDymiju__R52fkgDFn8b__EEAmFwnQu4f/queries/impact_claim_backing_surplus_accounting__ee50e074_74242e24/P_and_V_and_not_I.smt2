; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc2749826_accountant_is_configured () Bool)
(declare-fun cc2749826_active_registration_exists_before () Bool)
(declare-fun cc2749826_backing_surplus_accounting_available () Bool)
(declare-fun cc2749826_hypercore_slot_active_after_action () Bool)
(declare-fun cc2749826_registered_slot_is_activated_strict_read () Bool)
(assert
 (= cc2749826_accountant_is_configured cc2749826_accountant_is_configured))
(assert
 (= cc2749826_active_registration_exists_before cc2749826_active_registration_exists_before))
(assert
 (= cc2749826_backing_surplus_accounting_available cc2749826_backing_surplus_accounting_available))
(assert
 (= cc2749826_hypercore_slot_active_after_action cc2749826_hypercore_slot_active_after_action))
(assert
 (= cc2749826_registered_slot_is_activated_strict_read cc2749826_registered_slot_is_activated_strict_read))
(define-fun report_preconditions () Bool (and cc2749826_accountant_is_configured
     (not cc2749826_active_registration_exists_before)
     (not cc2749826_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> (not cc2749826_backing_surplus_accounting_available)
    (=> (and cc2749826_accountant_is_configured
             cc2749826_registered_slot_is_activated_strict_read)
        cc2749826_backing_surplus_accounting_available)))
(define-fun report_effects () Bool (and (not cc2749826_backing_surplus_accounting_available)
     cc2749826_accountant_is_configured
     cc2749826_registered_slot_is_activated_strict_read
     (not cc2749826_backing_surplus_accounting_available)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
