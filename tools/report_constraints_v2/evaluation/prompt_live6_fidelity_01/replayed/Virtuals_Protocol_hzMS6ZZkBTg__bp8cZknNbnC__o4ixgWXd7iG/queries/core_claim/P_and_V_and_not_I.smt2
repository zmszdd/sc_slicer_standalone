; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun update_impact_publicly_callable () Bool)
(declare-fun mint_recorded_latest_service () Bool)
(declare-fun external_call_possible () Bool)
(declare-fun service_impact_after () Int)
(declare-fun zero_impact () Int)
(assert
 (= update_impact_publicly_callable update_impact_publicly_callable))
(assert
 (= mint_recorded_latest_service mint_recorded_latest_service))
(assert
 (= external_call_possible external_call_possible))
(assert
 (= service_impact_after service_impact_after))
(assert
 (= zero_impact zero_impact))
(define-fun report_preconditions () Bool (and update_impact_publicly_callable
     mint_recorded_latest_service
     external_call_possible))
(define-fun report_safety () Bool (=> (and update_impact_publicly_callable
         mint_recorded_latest_service
         external_call_possible)
    (distinct service_impact_after zero_impact)))
(define-fun report_effects () Bool (and update_impact_publicly_callable
     mint_recorded_latest_service
     external_call_possible
     (not (distinct service_impact_after zero_impact))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
