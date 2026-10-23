; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6d980091_campaign_fields_update_blocked () Bool)
(declare-fun c6d980091_campaign_override_exists () Bool)
(declare-fun c6d980091_campaign_start_postponed () Bool)
(declare-fun c6d980091_configuration_update_allowed () Bool)
(declare-fun c6d980091_valid_configuration_update_requested () Bool)
(assert
 (= c6d980091_campaign_fields_update_blocked c6d980091_campaign_fields_update_blocked))
(assert
 (= c6d980091_campaign_override_exists c6d980091_campaign_override_exists))
(assert
 (= c6d980091_campaign_start_postponed c6d980091_campaign_start_postponed))
(assert
 (= c6d980091_configuration_update_allowed c6d980091_configuration_update_allowed))
(assert
 (= c6d980091_valid_configuration_update_requested c6d980091_valid_configuration_update_requested))
(define-fun report_preconditions () Bool c6d980091_campaign_start_postponed)
(define-fun report_safety () Bool (=> c6d980091_campaign_fields_update_blocked
    (=> (and c6d980091_campaign_override_exists
             c6d980091_valid_configuration_update_requested)
        c6d980091_configuration_update_allowed)))
(define-fun report_effects () Bool (and c6d980091_campaign_fields_update_blocked
     c6d980091_campaign_override_exists
     c6d980091_valid_configuration_update_requested
     (not c6d980091_configuration_update_allowed)))
(assert report_preconditions)
(check-sat)
(get-model)
