; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c53e3b186_campaign_override_exists () Bool)
(declare-fun c53e3b186_campaign_start_postponed () Bool)
(declare-fun c53e3b186_override_campaign_allowed () Bool)
(declare-fun c53e3b186_override_campaign_not_allowed_observed () Bool)
(assert
 (= c53e3b186_campaign_override_exists c53e3b186_campaign_override_exists))
(assert
 (= c53e3b186_campaign_start_postponed c53e3b186_campaign_start_postponed))
(assert
 (= c53e3b186_override_campaign_allowed c53e3b186_override_campaign_allowed))
(assert
 (= c53e3b186_override_campaign_not_allowed_observed c53e3b186_override_campaign_not_allowed_observed))
(define-fun report_preconditions () Bool c53e3b186_campaign_start_postponed)
(define-fun report_safety () Bool (=> c53e3b186_override_campaign_not_allowed_observed
    (=> (and c53e3b186_campaign_start_postponed
             c53e3b186_campaign_override_exists)
        c53e3b186_override_campaign_allowed)))
(define-fun report_effects () Bool (and c53e3b186_override_campaign_not_allowed_observed
     c53e3b186_campaign_start_postponed
     c53e3b186_campaign_override_exists
     (not c53e3b186_override_campaign_allowed)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
