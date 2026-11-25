; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c62794751_notified_emissions_should_be_tracked () Bool)
(declare-fun c62794751_notified_emissions_tracked () Bool)
(declare-fun c62794751_unclaimable_funds_created () Bool)
(declare-fun c62794751_voter_total_weight () Int)
(assert
 (= c62794751_notified_emissions_should_be_tracked c62794751_notified_emissions_should_be_tracked))
(assert
 (= c62794751_notified_emissions_tracked c62794751_notified_emissions_tracked))
(assert
 (= c62794751_unclaimable_funds_created c62794751_unclaimable_funds_created))
(assert
 (= c62794751_voter_total_weight c62794751_voter_total_weight))
(define-fun report_preconditions () Bool (and (= 0 c62794751_voter_total_weight) c62794751_notified_emissions_tracked))
(define-fun report_safety () Bool (= c62794751_notified_emissions_tracked
   c62794751_notified_emissions_should_be_tracked))
(define-fun report_effects () Bool (and c62794751_notified_emissions_tracked
     (not (= c62794751_notified_emissions_tracked
             c62794751_notified_emissions_should_be_tracked))
     c62794751_unclaimable_funds_created))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
