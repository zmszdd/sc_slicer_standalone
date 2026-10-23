; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c126db11b_accountant_is_configured () Bool)
(declare-fun c126db11b_accounting_reads_and_settlement_succeed () Bool)
(declare-fun c126db11b_active_registration_exists_for_target_slot () Bool)
(declare-fun c126db11b_slot_is_activated_strict_read () Bool)
(assert
 (= c126db11b_accountant_is_configured c126db11b_accountant_is_configured))
(assert
 (= c126db11b_accounting_reads_and_settlement_succeed c126db11b_accounting_reads_and_settlement_succeed))
(assert
 (= c126db11b_active_registration_exists_for_target_slot c126db11b_active_registration_exists_for_target_slot))
(assert
 (= c126db11b_slot_is_activated_strict_read c126db11b_slot_is_activated_strict_read))
(define-fun report_preconditions () Bool (and c126db11b_accountant_is_configured
     (not c126db11b_active_registration_exists_for_target_slot)))
(define-fun report_safety () Bool (=> (not c126db11b_accounting_reads_and_settlement_succeed)
    (=> (and c126db11b_accountant_is_configured
             c126db11b_slot_is_activated_strict_read)
        c126db11b_accounting_reads_and_settlement_succeed)))
(define-fun report_effects () Bool (and (not c126db11b_accounting_reads_and_settlement_succeed)
     c126db11b_accountant_is_configured
     c126db11b_slot_is_activated_strict_read
     (not c126db11b_accounting_reads_and_settlement_succeed)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
