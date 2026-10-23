; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0b500656_backing_reads_available () Bool)
(declare-fun c0b500656_core_accounting_reads_revert_observed () Bool)
(declare-fun c0b500656_corewriter_action_accepted () Bool)
(declare-fun c0b500656_pm_enabled () Bool)
(declare-fun c0b500656_registry_manually_cleaned_up () Bool)
(assert
 (= c0b500656_backing_reads_available c0b500656_backing_reads_available))
(assert
 (= c0b500656_core_accounting_reads_revert_observed c0b500656_core_accounting_reads_revert_observed))
(assert
 (= c0b500656_corewriter_action_accepted c0b500656_corewriter_action_accepted))
(assert
 (= c0b500656_pm_enabled c0b500656_pm_enabled))
(assert
 (= c0b500656_registry_manually_cleaned_up c0b500656_registry_manually_cleaned_up))
(define-fun report_preconditions () Bool (and c0b500656_corewriter_action_accepted c0b500656_pm_enabled))
(define-fun report_safety () Bool (=> (and c0b500656_core_accounting_reads_revert_observed
         (not c0b500656_registry_manually_cleaned_up))
    (=> (and c0b500656_corewriter_action_accepted c0b500656_pm_enabled)
        c0b500656_backing_reads_available)))
(define-fun report_effects () Bool (and c0b500656_core_accounting_reads_revert_observed
     (not c0b500656_registry_manually_cleaned_up)
     c0b500656_corewriter_action_accepted
     c0b500656_pm_enabled
     (not c0b500656_backing_reads_available)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
