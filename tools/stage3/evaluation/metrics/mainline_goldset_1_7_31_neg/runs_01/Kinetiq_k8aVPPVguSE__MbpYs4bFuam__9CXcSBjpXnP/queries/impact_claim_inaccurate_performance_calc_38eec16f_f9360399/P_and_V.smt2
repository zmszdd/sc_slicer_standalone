; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c14236392_generate_performance_proceeds () Bool)
(declare-fun c14236392_inaccurate_performance_calculations_occur () Bool)
(declare-fun c14236392_multiple_active_oracles () Bool)
(declare-fun c14236392_oracle_call_fails () Bool)
(declare-fun c14236392_sufficient_responses_met () Bool)
(assert
 (= c14236392_generate_performance_proceeds c14236392_generate_performance_proceeds))
(assert
 (= c14236392_inaccurate_performance_calculations_occur c14236392_inaccurate_performance_calculations_occur))
(assert
 (= c14236392_multiple_active_oracles c14236392_multiple_active_oracles))
(assert
 (= c14236392_oracle_call_fails c14236392_oracle_call_fails))
(assert
 (= c14236392_sufficient_responses_met c14236392_sufficient_responses_met))
(define-fun report_preconditions () Bool (and c14236392_multiple_active_oracles
     c14236392_oracle_call_fails
     c14236392_sufficient_responses_met))
(define-fun report_safety () Bool (not c14236392_generate_performance_proceeds))
(define-fun report_effects () Bool (and c14236392_sufficient_responses_met
     c14236392_generate_performance_proceeds
     c14236392_inaccurate_performance_calculations_occur))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
