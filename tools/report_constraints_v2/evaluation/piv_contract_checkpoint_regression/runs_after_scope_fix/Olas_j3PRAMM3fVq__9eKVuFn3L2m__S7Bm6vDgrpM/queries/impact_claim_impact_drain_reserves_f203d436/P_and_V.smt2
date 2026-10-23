; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7c5ef70e_guard_passes_manipulated_price () Bool)
(declare-fun c7c5ef70e_oracle_used_by_flows () Bool)
(declare-fun c7c5ef70e_reserves_drained_at_attacker_prices () Bool)
(declare-fun c7c5ef70e_spot_price_manipulable () Bool)
(assert
 (= c7c5ef70e_guard_passes_manipulated_price c7c5ef70e_guard_passes_manipulated_price))
(assert
 (= c7c5ef70e_oracle_used_by_flows c7c5ef70e_oracle_used_by_flows))
(assert
 (= c7c5ef70e_reserves_drained_at_attacker_prices c7c5ef70e_reserves_drained_at_attacker_prices))
(assert
 (= c7c5ef70e_spot_price_manipulable c7c5ef70e_spot_price_manipulable))
(define-fun report_preconditions () Bool (and c7c5ef70e_spot_price_manipulable c7c5ef70e_oracle_used_by_flows))
(define-fun report_safety () Bool (=> (and c7c5ef70e_spot_price_manipulable c7c5ef70e_oracle_used_by_flows)
    (and (not c7c5ef70e_guard_passes_manipulated_price)
         (not c7c5ef70e_reserves_drained_at_attacker_prices))))
(define-fun report_effects () Bool (and c7c5ef70e_spot_price_manipulable
     c7c5ef70e_oracle_used_by_flows
     (not (and (not c7c5ef70e_guard_passes_manipulated_price)
               (not c7c5ef70e_reserves_drained_at_attacker_prices)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
