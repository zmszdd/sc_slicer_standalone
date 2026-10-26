; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c31a0027f_atoken_total_supply () Int)
(declare-fun c31a0027f_attacker_other_synth_balance () Int)
(declare-fun c31a0027f_bank_run_defense_defeated () Bool)
(declare-fun c31a0027f_cap_bypass_path_reachable () Bool)
(declare-fun c31a0027f_other_synth_total_supply () Int)
(declare-fun c31a0027f_redeeming_full_supply_of_both () Bool)
(declare-fun c31a0027f_ztoken_total_supply () Int)
(assert
 (= c31a0027f_atoken_total_supply c31a0027f_atoken_total_supply))
(assert
 (= c31a0027f_attacker_other_synth_balance c31a0027f_attacker_other_synth_balance))
(assert
 (= c31a0027f_bank_run_defense_defeated c31a0027f_bank_run_defense_defeated))
(assert
 (= c31a0027f_cap_bypass_path_reachable c31a0027f_cap_bypass_path_reachable))
(assert
 (= c31a0027f_other_synth_total_supply c31a0027f_other_synth_total_supply))
(assert
 (= c31a0027f_redeeming_full_supply_of_both c31a0027f_redeeming_full_supply_of_both))
(assert
 (= c31a0027f_ztoken_total_supply c31a0027f_ztoken_total_supply))
(define-fun report_preconditions () Bool (and (or (= 0 c31a0027f_atoken_total_supply)
         (= 0 c31a0027f_ztoken_total_supply))
     (= c31a0027f_attacker_other_synth_balance
        c31a0027f_other_synth_total_supply)))
(define-fun report_safety () Bool (=> c31a0027f_cap_bypass_path_reachable c31a0027f_redeeming_full_supply_of_both))
(define-fun report_effects () Bool c31a0027f_bank_run_defense_defeated)
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
